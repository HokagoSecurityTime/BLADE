from pathlib import Path

p = Path('dashboard/src/main.jsx')
s = p.read_text(encoding='utf-8')
s = s.replace("['review','◇','수동 검토 큐']].map", "['review','◇','수동 검토 큐'],['settings','⚙','알림 설정']].filter(([id])=>id!=='settings'||features.alerts).map")
s = s.replace('`${p.id} ?? ??`', '`${p.id} 모드 전환`').replace("'observe? ??':'enforce? ??'", "'observe로 전환':'enforce로 전환'")
s = s.replace('<th>상태</th><th>관리</th>', '<th>상태</th>{features.mode&&<th>모드 / 버전</th>}<th>관리</th>')
s = s.replace('<th>정책 / 사유</th></tr>', '<th>정책 / 사유</th>{features.explain&&<th>설명</th>}</tr>')
s = s.replace('v{p.version} ? {p.source}', 'v{p.version} · {p.source}').replace("' ? would_block'", "' · would_block'").replace("l.explanation||'?'", "l.explanation||'—'")
s = s.replace('<p>id · created_at · status는 유지하세요.', '''<div className="editortabs"><button className={tab==='yaml'?'primary':''} onClick={()=>setTab('yaml')}>YAML</button>{features.reanalysis&&<button className={tab==='proposals'?'primary':''} onClick={()=>setTab('proposals')}>제안</button>}</div>{tab==='proposals'?<Proposals policy={edit} api={api} onChanged={refresh}/>:<>{features.rag&&<div className="evidence"><h3>근거 CVE</h3>{(edit.evidence_refs||[]).filter(r=>r.kind==='cve').map(r=><article key={r.ref}><b>{r.ref}</b><p>{r.snippet}</p></article>)}{!(edit.evidence_refs||[]).some(r=>r.kind==='cve')&&<p>이 정책이 인용한 CVE 근거가 없습니다.</p>}</div>}<p>id · created_at · status는 유지하세요.''')
s = s.replace('YAML 저장</button></div></section></div>', 'YAML 저장</button></div></>}</section></div>')
p.write_text(s, encoding='utf-8')
