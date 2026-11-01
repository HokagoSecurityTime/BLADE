from pathlib import Path
p=Path('dashboard/src/main.jsx')
s=p.read_text(encoding='utf-8').replace('import {Proposals, Observability}', 'import {Proposals, Observability, Evidence}')
s=s.replace("<div className=\"editortabs\"><button", "<div className=\"editortabs\">{features.rag&&<button className={tab==='cve'?'primary':''} onClick={()=>setTab('cve')}>근거 CVE</button>}<button")
s=s.replace("{tab==='proposals'?<Proposals", "{tab==='cve'?<Evidence policy={edit} api={api}/>:tab==='proposals'?<Proposals")
start=s.index('{features.rag&&<div className="evidence">')
end=s.index('<p>id ·',start)
s=s[:start]+s[end:]
p.write_text(s,encoding='utf-8')
