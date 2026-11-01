"""Apply the user's code+idiom selection without emitting any existing secrets."""
from pathlib import Path
import re

for path in (Path('.env'), Path('.env.example')):
    text = path.read_text(encoding='utf-8-sig') if path.exists() else ''
    line = 'BLADE_RAG_KINDS=code,idiom'
    text = re.sub(r'(?m)^BLADE_RAG_KINDS=.*$', line, text) if re.search(r'(?m)^BLADE_RAG_KINDS=', text) else text.rstrip()+'\n'+line+'\n'
    path.write_text(text, encoding='utf-8')
print('BLADE_RAG_KINDS set to code,idiom in .env and .env.example; no other values displayed')
