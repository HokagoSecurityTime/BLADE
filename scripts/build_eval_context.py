"""Static source context overlay. Never execute repositories or consume their labels."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from pipeline.parsers.erd import parse_erd
from scripts.eval_classifier import endpoint_input, build_user_prompt

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'datasets/blade/raw/vuln_apis'
OUT = ROOT / 'reports/eval/context'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source(path, line=1):
    return dict(file=path.relative_to(ROOT).as_posix(), line=line, sha256=sha(path))


def js_objects(path):
    """Parse literal object keys, not nested validators/default expressions."""
    from tree_sitter import Language, Parser
    import tree_sitter_typescript
    data = path.read_bytes()
    tree = Parser(Language(tree_sitter_typescript.language_typescript())).parse(data)
    def walk(node):
        yield node
        for child in node.named_children:
            yield from walk(child)
    return list(walk(tree.root_node))


def fields(node):
    result = {}
    for pair in node.named_children:
        if pair.type != 'pair':
            continue
        key = pair.child_by_field_name('key')
        value = pair.child_by_field_name('value')
        name = key.text.decode().strip('\'"')
        if re.fullmatch(r'[A-Za-z_]\w*', name):
            result[name] = (value.text.decode(), pair.start_point.row + 1)
    return result


def catalog():
    tables = []
    def add(service, name, cols, path, kind='relational', primary=()):
        if not cols:
            return
        tables.append(dict(service=service, table=name, kind=kind, columns=list(cols),
            primary=list(primary), provenance=[{**source(path, line), 'column': col} for col, line in cols.items()]))
    for path in sorted((RAW/'VAmPI/models').glob('*.py')):
        text = path.read_text(encoding='utf-8')
        for cls in ast.walk(ast.parse(text)):
            if not isinstance(cls, ast.ClassDef):
                continue
            name, cols, pk = None, {}, []
            for n in cls.body:
                if not isinstance(n, ast.Assign) or not isinstance(n.targets[0], ast.Name):
                    continue
                key = n.targets[0].id
                if key == '__tablename__':
                    name = ast.literal_eval(n.value)
                elif isinstance(n.value, ast.Call) and ast.unparse(n.value.func) == 'db.Column':
                    cols[key] = n.lineno
                    if any(k.arg == 'primary_key' and isinstance(k.value, ast.Constant) and k.value.value is True for k in n.value.keywords):
                        pk.append(key)
            if name:
                add('VAmPI', name, cols, path, primary=pk)
    for path in sorted((RAW/'juice-shop/models').glob('*.ts')):
        text = path.read_text(encoding='utf-8')
        name = re.search(r"tableName:\s*['\"]([^'\"]+)", text)
        if not name:
            continue
        for node in js_objects(path):
            if node.type != 'call_expression':
                continue
            fn = node.child_by_field_name('function')
            args = node.child_by_field_name('arguments')
            if fn and fn.text.decode().endswith('.init') and args.named_children[0].type == 'object':
                fs = fields(args.named_children[0])
                add('juice-shop', name[1], {k: v[1] for k, v in fs.items()}, path,
                    primary=[k for k,v in fs.items() if re.search(r'primaryKey:\s*true', v[0])])
    # Only explicit JPA table and column names plus unambiguous lowercase scalar fields.
    for path in sorted((RAW/'crAPI/services/identity/src/main/java/com/crapi/entity').glob('*.java')):
        text = path.read_text(encoding='utf-8')
        name = re.search(r'@Table\(name\s*=\s*"([^"]+)"', text)
        if not name:
            continue
        cols, pk = {}, []
        for match in re.finditer(r'((?:\s*@[^;]+?)?)\s+private\s+([\w<>]+)\s+(\w+)\s*;', text):
            annotation, typ, field = match.groups()
            explicit = re.search(r'@(?:Column|JoinColumn)\(name\s*=\s*"([^"]+)"', annotation)
            if '@Transient' in annotation:
                continue
            col = explicit[1] if explicit else field if field.islower() and typ in {'long','int','boolean','String','Long','Integer','UUID','EStatus'} else None
            if col:
                cols[col] = text[:match.start()].count('\n') + 1
                if re.search(r'@Id\b', annotation):
                    pk.append(col)
        add('crAPI', name[1], cols, path, primary=pk)
    # Current Django model declarations, avoiding stale migration-only columns.
    for path in sorted((RAW/'crAPI/services/workshop/crapi').glob('*/models.py')):
        for cls in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if not isinstance(cls, ast.ClassDef):
                continue
            name, cols, pk = None, {}, []
            for meta in cls.body:
                if isinstance(meta, ast.ClassDef) and meta.name == 'Meta':
                    for n in meta.body:
                        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'db_table':
                            name = ast.literal_eval(n.value)
                if not isinstance(meta, ast.Assign) or not isinstance(meta.targets[0], ast.Name) or not isinstance(meta.value, ast.Call):
                    continue
                fn = ast.unparse(meta.value.func)
                if (not fn.startswith('models.') and fn not in {'ForeignKey', 'OneToOneField'}) or fn.endswith('ManyToManyField'):
                    continue
                kw = {k.arg: k.value for k in meta.value.keywords}
                col = ast.literal_eval(kw['db_column']) if 'db_column' in kw else meta.targets[0].id + ('_id' if fn.endswith(('ForeignKey','OneToOneField')) else '')
                cols[col] = meta.lineno
                if 'primary_key' in kw and ast.literal_eval(kw['primary_key']):
                    pk.append(col)
            if name:
                add('crAPI', name, cols, path, primary=pk)
    # Mongo schema is represented as logical field inventory, not a real SQL schema.
    for path in sorted((RAW/'DVWS-node/src/models').glob('*.js')):
        text = path.read_text(encoding='utf-8')
        name = re.search(r"mongoose.model\(['\"]([^'\"]+)", text)
        if not name:
            continue
        for node in js_objects(path):
            if node.type == 'new_expression' and node.child_by_field_name('constructor').text == b'Schema':
                args = node.child_by_field_name('arguments')
                if args.named_children[0].type == 'object':
                    add('DVWS-node', name[1], {k:v[1] for k,v in fields(args.named_children[0]).items()}, path, 'mongo_model_fields')
    path = RAW/'Pixi/api/api.js'
    for node in js_objects(path):
        if node.type != 'call_expression':
            continue
        fn = node.child_by_field_name('function')
        match = re.fullmatch(r"db\.collection\(['\"]([^'\"]+)['\"]\)\.insert", fn.text.decode() if fn else '')
        args = node.child_by_field_name('arguments')
        if match and args.named_children and args.named_children[0].type == 'object':
            add('Pixi', match[1], {k:v[1] for k,v in fields(args.named_children[0]).items()}, path, 'mongo_insert_fields')
    # Sequelize relationships explicitly declare their FK column and target model.
    relations = RAW/'juice-shop/models/relations.ts'
    aliases = {}
    for t in tables:
        if t['service'] == 'juice-shop':
            p = ROOT/t['provenance'][0]['file']
            match = re.search(r'export\s*\{\s*\w+\s+as\s+(\w+)', p.read_text(encoding='utf-8'))
            if match:
                aliases[match[1]] = t
    text = relations.read_text(encoding='utf-8')
    for match in re.finditer(r'(\w+)\.belongsTo\((\w+),\s*\{[\s\S]*?name:\s*[\'"]([^\'"]+)[\s\S]*?\n\s*\}\)', text):
        origin, target, col = match.groups()
        if origin in aliases and target in aliases and col in aliases[origin]['columns'] and len(aliases[target]['primary']) == 1:
            aliases[origin].setdefault('foreign_keys', []).append(dict(column=col, table=aliases[target]['table'],
                ref_column=aliases[target]['primary'][0], provenance=source(relations, text[:match.start()].count('\n')+1)))
    return tables


def main():
    import os
    os.environ.update(BLADE_CONTROLLER_ENABLED='true', BLADE_PHASE2_ENABLED='true', BLADE_PROMPT_VERSION='v2.0')
    test = ROOT/'datasets/blade/processed/test.jsonl'
    before = sha(test)
    rows = [json.loads(s) for s in test.read_text(encoding='utf-8').splitlines()]
    tables = catalog()
    overlay, counts = [], Counter()
    for row in rows:
        if row['source'] != 'vuln':
            continue
        entry = dict(id=row['id'], provenance=[])
        selected = [t for t in tables if t['service'] == row['service']]
        # crAPI has independent persistence backends; do not mix their schemas.
        if row['service'] == 'crAPI':
            area = 'identity' if row['path'].startswith('/identity/') else 'workshop' if row['path'].startswith('/workshop/') else None
            selected = [t for t in selected if area and f'/services/{area}/' in t['provenance'][0]['file']]
        merged, primary, fks = {}, {}, {}
        for t in selected:
            merged.setdefault(t['table'], set()).update(t['columns'])
            primary.setdefault(t['table'], set()).update(t['primary'])
            fks.setdefault(t['table'], []).extend(t.get('foreign_keys', []))
            entry['provenance'].append(t)
        if merged:
            ddl = '\n'.join('CREATE TABLE "'+name+'" ('+', '.join(
                ['"'+c+'" TEXT' for c in sorted(cols)] +
                (['PRIMARY KEY ('+', '.join('"'+c+'"' for c in sorted(primary[name]))+')'] if primary[name] else []) +
                ['FOREIGN KEY ("'+f['column']+'") REFERENCES "'+f['table']+'" ("'+f['ref_column']+'")' for f in fks[name] if f['table'] in merged]
                )+');' for name,cols in sorted(merged.items()))
            parse_erd(ddl)
            entry['erd_snippet'] = ddl
            counts[row['service']+':erd_added'] += 1
        texts = []
        if row['service'] == 'juice-shop':
            registration = RAW/'juice-shop/server.ts'
            texts.append(registration.read_text(encoding='utf-8'))
            entry['provenance'].append(dict(controller=source(registration)))
        for loc in row.get('meta', {}).get('source_locations', []):
            path = (RAW/row['service']/loc['file']).resolve()
            if path.is_relative_to((RAW/row['service']).resolve()) and path.is_file():
                texts.append(path.read_text(encoding='utf-8-sig'))
                entry['provenance'].append(dict(controller=source(path, loc.get('start_line',1))))
        if texts:
            entry['controller_text'] = '\n\n'.join(dict.fromkeys(texts))
            counts[row['service']+':source_files_mapped'] += 1
        endpoint, erd, _ = endpoint_input({**row, **entry})
        payload = json.loads(build_user_prompt(endpoint, erd, entry.get('controller_text', row.get('controller_text')), []))
        counts[row['service']+(':handler_parsed' if payload.get('controller_text') else ':handler_unmapped')] += 1
        overlay.append(entry)
    assert sha(test) == before
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'source_overlay.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in overlay), encoding='utf-8')
    report = dict(test_sha256=before, counts=dict(counts), catalog=tables,
        limitations=['TEXT is a type-neutral carrier; real database types/constraints are not reconstructed.',
        'Mongo entries are logical model/insert field inventories, not relational tables or verified collection names for Mongoose.',
        'Only explicit Sequelize FK relationships are retained; no implicit columns, naming aliases or authorization checks invented.',
        'Java/Go/Flask unsupported handlers remain missing in runtime prompts.',
        'crAPI community Mongo mapping remains unavailable; no guessed schema injected.'])
    (OUT/'source_context_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    lines = ['# 소스 기반 평가 입력 보강', '',
        '고정 test의 라벨·경로·OAS는 변경하지 않는다. 별도 overlay에는 ERD와 controller 원문 및 출처만 저장한다.', '',
        '| Service | ERD 추가 | 원문 소스 매핑 | 런타임 경로 파싱 | 경로 미매핑 |', '|---|---:|---:|---:|---:|']
    for service in ['VAmPI','crAPI','juice-shop','Pixi','DVWS-node']:
        lines.append('| '+service+' | '+' | '.join(str(counts[service+':'+k]) for k in ['erd_added','source_files_mapped','handler_parsed','handler_unmapped'])+' |')
    lines += ['', '## 추출 범위와 한계', '',
        '- SQLAlchemy 명시 컬럼, Sequelize init·관계 선언, JPA 명시 이름 및 단순 필드, Django 현재 모델, Mongoose Schema, Pixi insert 객체 키를 정적 분석했다.',
        '- 공개 API 211건 중 205건에 필드 목록을 제공한다. crAPI community 6건은 미보강이다. 합성 42건은 기존 입력을 유지한다.',
        '- 테이블 타입은 TEXT로 통일한 파서 전달용 표현이다. 실제 타입이나 완전한 DB DDL을 복원했다고 주장하지 않는다. 명시 PK 및 확인한 Sequelize FK만 보존한다.',
        '- MongoDB는 컬렉션/모델 필드 목록을 DDL 형태로 표현한다. 특히 Mongoose 모델명은 실제 컬렉션명과 다를 수 있어 정책 실행용 lookup으로 검증된 이름이 아니다.',
        '- service 전체 모델을 전달하며 crAPI는 identity/workshop 저장소 범위를 분리한다. 엔드포인트별 실제 접근 테이블을 모두 증명한 매핑은 아니다.',
        '- 원래 meta.source_locations의 실제 파일을 연결한다. Juice Shop server.ts의 라우트 등록도 포함한다. 인가 검사나 가짜 데코레이터를 만들지 않는다.',
        '- 경로 파싱 성공은 함수 호출을 따라 모든 인가 검사를 읽은 성공률이 아니다. factory handler·Java/Go·Flask·Express router.route 체인은 여전히 불완전하다.',
        '- 원문 파일 경로·줄·SHA-256은 source_context_report.json 및 source_overlay.jsonl에 기록한다. 공개 저장소를 실행하거나 수정하지 않았다.']
    (OUT/'source_context_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(counts),ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
