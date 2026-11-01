"""One-time v2.0 extraction from the preserved pre-change source; no API calls."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
original = ROOT / 'verification/phase3/prompt_before_v2.py'
source = original.read_text(encoding='utf-8')
tree = ast.parse(source)
base = next(node for node in tree.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == 'SYSTEM_PROMPT' for target in node.targets))
controller = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_controller_system_prompt')
controller_text = next(node.value.right for node in ast.walk(controller)
                       if isinstance(node, ast.Return) and isinstance(node.value, ast.BinOp))
system = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'system_prompt')
rag_text = next(node.value for node in ast.walk(system) if isinstance(node, ast.AugAssign))
data = dict(version='v2.0', system=ast.literal_eval(base.value),
            controller_extension=ast.literal_eval(controller_text), rag_extension=ast.literal_eval(rag_text),
            user_template={'output_format': 'json', 'endpoint': '$endpoint', 'tables': '$tables',
                           'object_bindings': '$object_bindings', 'controller_text': '$controller_text'})
payload = json.dumps(data, ensure_ascii=False, indent=2)
digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()
target = ROOT / 'prompts/v2.0.md'
target.parent.mkdir(exist_ok=True)
text = (f'SHA-256: {digest}\nSnapshot-UTC: {datetime.now(timezone.utc).isoformat()}\n'
        f'Source-SHA-256: {hashlib.sha256(original.read_bytes()).hexdigest()}\n\n'
        '# BLADE prompt v2.0\n\nSHA-256 covers exactly the UTF-8 JSON block content below, without its final newline. '
        'Strings preserve original whitespace. User placeholders are filled with structured values in insertion order; '
        'optional controller/RAG fields are assembled by the existing builder. '
        'Immutable snapshot: future edits require a new version file.\n\n```json\n' + payload + '\n```\n')
with target.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(text)
# Replace only prompt constants; dynamic assembly logic stays in the runtime.
source = source.replace(ast.get_source_segment(source, base), 'SYSTEM_PROMPT = prompt_bundle()["system"]')
source = source.replace(ast.get_source_segment(original.read_text(encoding='utf-8'), controller_text), 'prompt_bundle()["controller_extension"]')
source = source.replace(ast.get_source_segment(original.read_text(encoding='utf-8'), rag_text), 'prompt_bundle()["rag_extension"]')
source = source.replace('from dataclasses import asdict', 'from dataclasses import asdict\nfrom pipeline.classifier.prompt_store import prompt_bundle')
source = source.replace('payload = {"output_format": "json", "endpoint": asdict(endpoint),\n'
                       '                       "tables": {name: asdict(table) for name, table in erd.items()},\n'
                       '                       "object_bindings": bindings,\n'
                       '                       "controller_text": controller_text}',
                       'values = {"endpoint": asdict(endpoint), "tables": {name: asdict(table) for name, table in erd.items()},\n'
                       '              "object_bindings": bindings, "controller_text": controller_text}\n'
                       '    payload = {key: values[value[1:]] if isinstance(value, str) and value.startswith("$") else value\n'
                       '               for key, value in prompt_bundle()["user_template"].items()}')
source = source.replace('return SYSTEM_PROMPT + ', 'return prompt_bundle()["system"] + ')
source = source.replace('return SYSTEM_PROMPT\n', 'return prompt_bundle()["system"]\n')
(ROOT / 'pipeline/classifier/prompt.py').write_text(source, encoding='utf-8', newline='\n')
print(digest)
