"""Pinned original handler/repository replay with SQLite and synthetic principals.

Not a deployment/JWT/PostgreSQL integration test. Upstream sources stay immutable.
"""
import ast
import copy
import hashlib
import html
import json
from pathlib import Path
import sqlite3
import sys
from types import SimpleNamespace as NS
from typing import Optional

from fastapi import Body, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from markdown_it import MarkdownIt
from training.experiments.external_condition_probe import ROOT, RAW
from training.experiments.fastapi_condition_adapter import Adapter

SQLROOT=ROOT/'datasets/blade/raw/self_account_sql_v1'
OUT=ROOT/'reports/eval/classification_quality/self_account_binding_v1'


def node(path,name):
    return next(n for n in ast.walk(ast.parse(path.read_text(encoding='utf8'))) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.name==name)


def compile_function(fn,namespace):
    clean=copy.deepcopy(fn);clean.decorator_list=[];clean.returns=None
    clean.args.defaults=[];clean.args.kw_defaults=[None]*len(clean.args.kwonlyargs)
    # Repository optional update fields retain their original None defaults.
    for i,d in enumerate(fn.args.kw_defaults):
        if isinstance(d,ast.Constant):clean.args.kw_defaults[i]=d
    for a in [*clean.args.args,*clean.args.kwonlyargs]:a.annotation=None
    exec(compile(ast.fix_missing_locations(ast.Module(body=[clean],type_ignores=[])),'<pinned-source-function>','exec'),namespace)
    return namespace[fn.name]


def sql_section(name):
    source=(SQLROOT/'app/db/queries/sql/users.sql').read_text(encoding='utf8')
    after=source.split('-- name: '+name,1)[1]
    return after.split('\n',1)[1].split('-- name:',1)[0].strip()


class Missing(Exception):pass


class Transaction:
    async def __aenter__(self):return self
    async def __aexit__(self,*args):return False


class Repository:
    def __init__(self,db):self.db=db;self.connection=self;self.calls=[]
    def transaction(self):return Transaction()
    async def get_user_by_username(self,*,username):
        row=self.db.execute(sql_section('get-user-by-username^'),{'username':username}).fetchone()
        if row is None:raise Missing()
        return NS(**dict(row))
    async def get_user_by_email(self,*,email):
        row=self.db.execute(sql_section('get-user-by-email^'),{'email':email}).fetchone()
        if row is None:raise Missing()
        return NS(**dict(row))


async def update_sql(connection,**params):
    connection.calls.append(dict(params))
    row=connection.db.execute(sql_section('update-user-by-username<!'),params).fetchone()
    return row['updated_at'] if row else None


def build_harness():
    wheelroot=ROOT/'verification/self_account_wheels'
    for dep in json.loads((wheelroot/'manifest.json').read_text(encoding='utf8')):
        wheel=wheelroot/dep['path']
        assert hashlib.sha256(wheel.read_bytes()).hexdigest()==dep['sha256']
        if str(wheel) not in sys.path:sys.path.insert(0,str(wheel))
    from pydantic.v1 import BaseModel,EmailStr,HttpUrl
    schema=node(RAW/'app/models/schemas/users.py','UserInUpdate')
    schema_ns=dict(BaseModel=BaseModel,Optional=Optional,EmailStr=EmailStr,HttpUrl=HttpUrl)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(schema)],type_ignores=[])),'<original-update-schema>','exec'),schema_ns)
    Update=schema_ns['UserInUpdate']
    db=sqlite3.connect(':memory:',check_same_thread=False);db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE users (id INTEGER PRIMARY KEY,username TEXT UNIQUE,email TEXT UNIQUE,salt TEXT,hashed_password TEXT,bio TEXT,image TEXT,created_at TEXT,updated_at TEXT)')
    for i,name in enumerate(['alice','bob'],1):db.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?)',(i,name,name+'@example.com','salt','hash','original-'+name,None,'initial','initial'))
    repo=Repository(db)
    namespace=dict(EntityDoesNotExist=Missing,HTTPException=HTTPException,HTTP_400_BAD_REQUEST=400,
        queries=NS(update_user_by_username=update_sql),str=str,
        jwt=NS(create_access_token_for_user=lambda *args:'test-token'),UserInResponse=NS,UserWithToken=NS,
        strings=NS(USERNAME_TAKEN='username taken',EMAIL_TAKEN='email taken'))
    for name in ['check_username_is_taken','check_email_is_taken']:
        compile_function(node(RAW/'app/services/authentication.py',name),namespace)
    repo_fn=compile_function(node(RAW/'app/db/repositories/users.py','update_user'),namespace)
    repo.update_user=repo_fn.__get__(repo,Repository)
    get_fn=compile_function(node(RAW/'app/api/routes/users.py','retrieve_current_user'),namespace)
    put_fn=compile_function(node(RAW/'app/api/routes/users.py','update_current_user'),namespace)
    settings=NS(secret_key=NS(get_secret_value=lambda:'dummy'))
    app=FastAPI()
    async def principal(name):return await repo.get_user_by_username(username=name)
    @app.get('/user')
    async def get(x_actor:str=Header('alice')):
        return await get_fn(user=await principal(x_actor),settings=settings)
    @app.put('/user')
    async def put(user:dict=Body(...,embed=True),x_actor:str=Header('alice')):
        return await put_fn(user_update=Update(**user),current_user=await principal(x_actor),users_repo=repo,settings=settings)
    return app,repo,db


def main():
    for root in [RAW,SQLROOT]:
        manifest=json.loads((root/'manifest.json').read_text(encoding='utf8'))
        for f in manifest['files']:assert hashlib.sha256((root/f['path']).read_bytes()).hexdigest()==f['sha256']
    adapter=Adapter(RAW)
    p=RAW/'app/api/routes/users.py';put=node(p,'update_current_user')
    sink=next(n for n in ast.walk(put) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='update_user')
    assert any(k.arg=='user' and isinstance(k.value,ast.Name) and k.value.id=='current_user' for k in sink.keywords)
    cases=[
        ('GET', '?id=2&user_id=2&username=bob',None,200,'alice'),
        ('PUT','',{'id':2,'bio':'changed'},200,'alice'),
        ('PUT','',{'user_id':2,'bio':'changed'},200,'alice'),
        ('PUT','',{'owner_id':'bob','bio':'changed'},200,'alice'),
        ('PUT','',{'user':{'username':'bob'},'bio':'changed'},200,'alice'),
        ('PUT','?username=bob&id=2',{'bio':'changed'},200,'alice'),
        ('PUT','',{'username':'bob','bio':'changed'},400,'alice'),
        ('PUT','',{'email':'bob@example.com','bio':'changed'},400,'alice'),
        ('PUT','',{'username':'alice_new','id':2,'bio':'changed'},200,'alice_new'),
    ]
    outcomes=[]
    for method,query,body,expected,newname in cases:
        app,repo,db=build_harness()
        before=dict(db.execute('SELECT * FROM users WHERE id=2').fetchone())
        with TestClient(app) as client:
            kwargs={} if body is None else {'json':{'user':body}}
            res=client.request(method,'/user'+query,headers={'x-actor':'alice'},**kwargs)
        after=dict(db.execute('SELECT * FROM users WHERE id=2').fetchone())
        alice=dict(db.execute('SELECT * FROM users WHERE id=1').fetchone())
        passed=res.status_code==expected and before==after and alice['username']==newname
        if method=='GET':passed=passed and res.json()['user']['username']=='alice'
        if method=='PUT' and expected==200:
            passed=passed and alice['bio']=='changed' and len(repo.calls)==1
        if expected==400:
            passed=passed and alice['bio']=='original-alice' and not repo.calls
        if repo.calls:passed=passed and all(c['username']=='alice' for c in repo.calls)
        outcomes.append(dict(method=method,query=query,body=body,expected_status=expected,actual_status=res.status_code,
            other_account_unchanged=before==after,self_account_bio=alice['bio'],
            sql_target_values=[c['username'] for c in repo.calls],passed=passed))
        db.close()
    OUT.mkdir(parents=True,exist_ok=True)
    refs=[adapter.ref(p,node(p,n)) for n in ['retrieve_current_user','update_current_user']]
    refs.append(adapter.ref(RAW/'app/db/repositories/users.py',node(RAW/'app/db/repositories/users.py','update_user')))
    result=dict(binding='authenticated current_user -> update_user(user=current_user) -> SQL WHERE username=:username',
        proposed_pattern='self_account_binding',existing_label_candidate='owner_match',final_label=None,
        outcomes=outcomes,evidence=refs,api_calls=0,
        limitations=['synthetic header principal; JWT not tested','SQLite rather than upstream PostgreSQL',
          'Pydantic v1 compatibility layer rather than exact upstream dependency lock',
          'JWT signing/response objects/connection and user loading are test doubles',
          'no production middleware or concurrent mutation testing'])
    (OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    text='# 本인 계정 바인딩 추출·타인 ID 주입 검사\n\n'.replace('本인','본인')
    text+='인증 사용자 → 핸들러 대상 → 저장소 대상 키 → SQL WHERE 연결을 확인했다. 요청에 넣은 id/user_id/owner_id는 수정 대상 키로 사용되지 않는다. username은 변경할 새 값이며 기존 대상 키와 다르다.\n\n'
    text+=f'격리 검사 **{sum(o["passed"] for o in outcomes)}/{len(outcomes)} 통과**. 모든 사례에서 다른 계정의 DB 행은 그대로였다.\n\n'
    text+='| 요청 | 주입값 | 상태 | 타인 계정 보존 |\n|---|---|---:|---|\n'
    for o in outcomes:text+=f'| {o["method"]} {o["query"]} | {json.dumps(o["body"],ensure_ascii=False)} | {o["actual_status"]} | {o["other_account_unchanged"]} |\n'
    text+='\n## 해석\n\n200 응답을 주입 차단 실패로 보지 않는다. 알 수 없는 필드는 원본 Update 스키마에서 무시되고 실제 대상은 인증 사용자로 유지된다. 이미 존재하는 다른 username/email로 변경하려는 요청은 원본 중복 검사에서 400으로 거부된다. 사용하지 않는 새 username으로 이름을 바꾸는 경우에도 동일한 사용자 행만 갱신된다.\n\n'
    text+='## 실행 범위\n\n원본 GET/PUT 핸들러·update_user 저장소 메서드·중복 검사 함수의 본문을 그대로 격리 실행했다. import·타입 annotation·Depends 기본값은 격리 호출을 위해 제거했다. 원본 UserInUpdate 스키마는 Pydantic v1 호환 모드로 실행했다. 같은 커밋의 원본 SQL을 SQLite에서 실행했으며 전체 PostgreSQL 앱 실행은 아니다. 인증 사용자는 테스트 헤더로 주입했고 JWT는 검증하지 않았다.\n\n'
    text+='## 라벨 처리\n\n요청자에게 대상을 고정하는 패턴을 구현 근거로 추가했다. 기존 owner_match의 후보로만 기록하며 새 8번째 라벨을 만들지 않았다. 최종 라벨·고정 test·학습 데이터·런타임은 변경하지 않았다. 다음은 생성자 귀속과 관계 레코드의 요청자 키 추적이다.\n'
    (OUT/'report.md').write_text(text,encoding='utf8')
    content=MarkdownIt('commonmark').enable('table').render(text)
    content+='<details><summary>검사 기록·근거</summary><pre>'+html.escape(json.dumps(result,ensure_ascii=False,indent=2))+'</pre></details>'
    (OUT/'report.htm').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>본인 계정 검증</title><style>body{max-width:1100px;margin:40px auto;padding:20px;font:16px/1.7 system-ui}td,th{padding:10px;border:1px solid #ccd}pre{white-space:pre-wrap}</style>'+content+'</html>',encoding='utf8')
    assert all(o['passed'] for o in outcomes)
    assert hashlib.sha256((ROOT/'datasets/blade/processed/test.jsonl').read_bytes()).hexdigest()=='bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa'
    print('self-account tests:',len(outcomes),'passed')


if __name__=='__main__':main()
