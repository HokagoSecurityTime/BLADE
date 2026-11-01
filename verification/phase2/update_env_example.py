from pathlib import Path
import re

p=Path('.env.example');text=p.read_text(encoding='utf-8')
settings={
    'BLADE_ALERTS_ENABLED':'true', 'BLADE_EXPLAIN_ENABLED':'true', 'BLADE_CVE_ENABLED':'true',
    'BLADE_REANALYSIS_ENABLED':'true', 'BLADE_REANALYSIS_OBSERVE_THRESHOLD':'20',
    'BLADE_REANALYSIS_MIN_REQUESTS':'5', 'BLADE_REANALYSIS_MIN_SUBJECTS':'3',
    'BLADE_REANALYSIS_WOULD_BLOCK_RATIO':'0.8', 'BLADE_REANALYSIS_POLL_SEC':'5',
    'NVD_API_KEY':''}
for name,value in settings.items():
    if not re.search(r'(?m)^'+name+'=',text):text=text.rstrip()+'\n'+name+'='+value+'\n'
p.write_text(text,encoding='utf-8')
print('Added missing Phase 2 settings to .env.example; existing values not displayed')
