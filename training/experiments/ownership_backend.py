"""Isolated development API; not imported by BLADE runtime."""
import sqlite3
from pathlib import Path

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict


class Entry(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str
    principal: str | None = None


def create_app(database: Path, secret: str):
    app = FastAPI()
    def connection():
        db = sqlite3.connect(database)
        db.row_factory = sqlite3.Row
        return db
    with connection() as db:
        db.executescript('CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY, principal TEXT NOT NULL, title TEXT NOT NULL); CREATE TABLE IF NOT EXISTS profiles (principal TEXT PRIMARY KEY, nickname TEXT NOT NULL);')

    def subject(authorization: str | None = Header(default=None)):
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(401)
        try:
            claims = jwt.decode(authorization[7:], secret, algorithms=['HS256'],
                audience='ownership-experiment', issuer='local-development', options={'require':['sub','exp','aud','iss']})
            if not isinstance(claims['sub'], str) or not claims['sub']:
                raise ValueError('invalid subject')
            return claims['sub']
        except (jwt.PyJWTError, ValueError):
            raise HTTPException(401)

    @app.get('/profile')
    def profile(who=Depends(subject)):
        with connection() as db:
            row = db.execute('SELECT principal,nickname FROM profiles WHERE principal=?', (who,)).fetchone()
        if row is None:
            raise HTTPException(404)
        return dict(row)

    @app.post('/entries', status_code=201)
    def create(body: Entry, who=Depends(subject)):
        if 'principal' in body.model_fields_set and body.principal != who:
            raise HTTPException(403)
        with connection() as db:
            cursor = db.execute('INSERT INTO entries(principal,title) VALUES (?,?)', (who,body.title))
            ident = cursor.lastrowid
        return dict(id=ident, principal=who, title=body.title)

    @app.get('/entries')
    def listing(offset: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100), who=Depends(subject)):
        with connection() as db:
            count = db.execute('SELECT count(*) FROM entries WHERE principal=?', (who,)).fetchone()[0]
            rows = db.execute('SELECT * FROM entries WHERE principal=? ORDER BY id LIMIT ? OFFSET ?', (who,limit,offset)).fetchall()
        return dict(total=count, items=[dict(r) for r in rows])

    @app.get('/entries/{ident}')
    def read(ident: int, who=Depends(subject)):
        with connection() as db:
            row = db.execute('SELECT * FROM entries WHERE id=? AND principal=?', (ident,who)).fetchone()
        if row is None:
            raise HTTPException(404)
        return dict(row)

    @app.put('/entries/{ident}')
    def update(ident: int, body: Entry, who=Depends(subject)):
        if 'principal' in body.model_fields_set and body.principal != who:
            raise HTTPException(403)
        with connection() as db:
            cursor = db.execute('UPDATE entries SET title=? WHERE id=? AND principal=?', (body.title,ident,who))
            if cursor.rowcount != 1:
                raise HTTPException(404)
        return {'updated': True}
    return app
