"""Verification-only launcher. Production sources/configuration are untouched."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'verification'
RUNTIME = OUT / 'presentation-runtime'
RUNTIME.mkdir(exist_ok=True)
(OUT / 'logs').mkdir(exist_ok=True)
paths = [p for folder in ('admin_api','proxy','common','demo_backend','pipeline','dashboard','scripts')
         for p in (ROOT/folder).rglob('*') if p.is_file() and not any(x in p.parts for x in ('__pycache__','node_modules','dist'))]
paths += [ROOT/'docker-compose.yml',ROOT/'Dockerfile',ROOT/'pyproject.toml',ROOT/'AGENT.md']
(OUT/'presentation-source-before.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2))
env = os.environ.copy()
for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines():
    if line.strip() and not line.lstrip().startswith('#') and '=' in line:
        key,value=line.split('=',1)
        env[key.strip()]=value.strip().strip('"').strip("'")
env.update(PYTHONPATH=str(ROOT),PYTHONUNBUFFERED='1',BLADE_TARGET_URL='http://127.0.0.1:9000',
           BLADE_ADMIN_URL='http://127.0.0.1:8100',BLADE_DB_DSN='sqlite:///'+str(RUNTIME/'demo.db'),
           BLADE_PROXY_HOST='127.0.0.1',BLADE_OLLAMA_URL='http://127.0.0.1:11434')
python=str(ROOT/'.python/python.exe')
services={
    'demo_backend':[python,'-m','uvicorn','demo_backend.main:app','--host','127.0.0.1','--port','9000'],
    'admin_api':[python,'-m','uvicorn','admin_api.main:app','--host','127.0.0.1','--port','8100'],
    'proxy':[python,'-m','proxy.server'],
}
processes={}
for name,command in services.items():
    with (OUT/'logs'/f'{name}.log').open('ab',buffering=0) as log:
        child=subprocess.Popen(command,cwd=RUNTIME,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                               creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
    processes[name]={'pid':child.pid,'command':command,'log':str(OUT/'logs'/f'{name}.log')}
(OUT/'presentation-processes.json').write_text(json.dumps(processes,indent=2))
print(json.dumps({name: data['pid'] for name,data in processes.items()}))
