from pathlib import Path
p=Path('dashboard/src/main.jsx');s=p.read_text(encoding='utf-8')
s=s.replace('onChanged={refresh}', "onChanged={async()=>{const current=await api('/policies/'+encodeURIComponent(edit.id));setEdit(current);setYaml(stringify(current));await refresh();}}")
p.write_text(s,encoding='utf-8')
