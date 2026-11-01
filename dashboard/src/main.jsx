import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {parse, stringify} from 'yaml';
import './style.css';
import {Proposals, Observability, Evidence} from './Phase2';

async function api(path, options={}) {
  const response = await fetch('/api'+path, {...options, headers:{'Content-Type':'application/json',...options.headers}});
  const body = await response.json();
  if (!response.ok) throw new Error(response.status === 409 ? '정책 상태가 변경되었습니다. 새로고침 후 다시 시도하세요.' : JSON.stringify(body.detail || body));
  return body;
}
const badge = value => <span className={'badge '+value}>{value}</span>;
const time = value => new Date(value).toLocaleString('ko-KR');

function AlertSettings() {
  const [settings,setSettings]=useState(null), [message,setMessage]=useState(''), [busy,setBusy]=useState(false);
  useEffect(()=>{api('/settings/alerts').then(setSettings).catch(e=>setMessage(e.message));},[]);
  async function submit(test=false) {
    setBusy(true);
    try {await api('/settings/alerts',{method:'PUT',body:JSON.stringify(settings)});const result=test?await api('/settings/alerts/test',{method:'POST'}):null;setMessage(test?(result.delivered?'테스트 알림이 전송되었습니다.':'전송 실패: 워커 로그와 webhook을 확인하세요.'):'설정을 저장했습니다.');}
    catch(e){setMessage(e.message);}finally{setBusy(false);}
  }
  return <div className="settingsform"><p>이 화면의 테스트 전송 버튼은 설정한 채널에 실제 메시지를 보냅니다.</p>{settings&&<>{['slack_webhook','discord_webhook'].map(k=><label key={k}>{k}<input type="password" autoComplete="off" value={settings[k]} onChange={e=>setSettings({...settings,[k]:e.target.value})}/></label>)}<label>알림 기준<select value={settings.min_severity} onChange={e=>setSettings({...settings,min_severity:e.target.value})}><option value="observe">차단 + 관측 위반</option><option value="block">실제 차단만</option></select></label><div className="actions"><button disabled={busy} onClick={()=>submit()}>설정 저장</button><button disabled={busy} onClick={()=>submit(true)}>저장 후 테스트 전송</button></div></>}{message&&<p role="status">{message}</p>}</div>;
}

function App() {
  const [features,setFeatures]=useState({}), [tab,setTab]=useState('yaml');
  const [page,setPage]=useState('policies'), [policies,setPolicies]=useState([]), [logs,setLogs]=useState([]);
  const [filter,setFilter]=useState('ALL'), [verdict,setVerdict]=useState('ALL');
  const [error,setError]=useState(''), [notice,setNotice]=useState(''), [updated,setUpdated]=useState(null);
  const [edit,setEdit]=useState(null), [yaml,setYaml]=useState(''), [busy,setBusy]=useState(false);
  async function refresh() {
    try {const [p,l]=await Promise.all([api('/policies'),api('/detections?limit=100')]);setPolicies(p);setLogs(l);setUpdated(new Date());setError('');}
    catch(e){setError(e.message);}
  }
  useEffect(()=>{api('/features').then(setFeatures).catch(()=>setFeatures({}));refresh(); const timer=setInterval(refresh,5000);return ()=>clearInterval(timer);},[]);
  async function action(p,verb) {
    setBusy(true);setNotice('');
    try {await api(`/policies/${encodeURIComponent(p.id)}/${verb}`,{method:'POST'});setNotice(`${p.id} · ${verb} 완료`);await refresh();}
    catch(e){setError(e.message);} finally{setBusy(false);}
  }
  async function mode(p){setBusy(true);try{await api(`/policies/${encodeURIComponent(p.id)}/mode`,{method:'POST',body:JSON.stringify({mode:p.mode==='enforce'?'observe':'enforce'})});await refresh();}catch(e){setError(e.message);}finally{setBusy(false);}}
  function open(p){setTab('yaml');setEdit(p);setYaml(stringify(p));setError('');}
  async function save() {
    setBusy(true);
    try {
      const data=parse(yaml);
      if (!data || typeof data!=='object' || Array.isArray(data)) throw new Error('정책 YAML 객체를 입력하세요.');
      if(data.id!==edit.id || data.created_at!==edit.created_at || data.status!==edit.status) throw new Error('id, created_at, status는 YAML에서 변경할 수 없습니다.');
      delete data.status;
      await api('/policies/'+encodeURIComponent(edit.id),{method:'PUT',body:JSON.stringify(data)});
      setEdit(null);setNotice('정책 YAML을 저장했습니다.');await refresh();
    } catch(e){setError(e.message);} finally{setBusy(false);}
  }
  const reviews=policies.filter(p=>p.label==='manual_review_required');
  const visible=policies.filter(p=>filter==='ALL'||p.status===filter);
  const titles={policies:['Policy management','정책 목록'],logs:['Detection stream','탐지 로그'],review:['Human in the loop','수동 검토 큐'],settings:['Notifications','알림 설정']};
  function controls(p){return <div className="actions"><button onClick={()=>open(p)}>YAML 보기·편집</button>{p.status==='PENDING'&&<><button className="primary" disabled={busy} onClick={()=>action(p,'approve')} aria-label={`${p.id} 승인`}>승인</button><button disabled={busy} onClick={()=>action(p,'reject')} aria-label={`${p.id} 거절`}>거절</button></>}{features.mode&&p.status==='ACTIVE'&&<button disabled={busy} onClick={()=>mode(p)} aria-label={`${p.id} 모드 전환`}>{p.mode==='enforce'?'observe로 전환':'enforce로 전환'}</button>}{p.status==='ACTIVE'&&<button disabled={busy} onClick={()=>action(p,'rollback')} aria-label={`${p.id} 롤백`}>롤백</button>}</div>}
  return <div className="layout">
    <aside><a className="brand" href="#">◈ BLADE<span>AUTHORIZATION INTELLIGENCE</span></a><div className="workspace"><span className="dot"/> Demo workspace <small>LOCAL ENVIRONMENT</small></div><p className="navlabel">WORKSPACE</p><nav>{[['policies','▦','정책 목록'],['logs','≋','탐지 로그'],['review','◇','수동 검토 큐'],['settings','⚙','알림 설정']].filter(([id])=>id!=='settings'||features.alerts).map(([id,icon,title])=><button key={id} className={page===id?'selected':''} onClick={()=>{setPage(id);setError('');}}><span>{icon}</span>{title}{id==='review'&&<b>{reviews.length}</b>}</button>)}</nav><footer>정책은 사람이 승인하고,<br/>BLADE는 요청을 보호합니다.<div>RUNTIME / NO LLM</div></footer></aside>
    <main><header><span>Workspace <i>/</i> {titles[page][1]}</span><span className="connection"><span className={'dot '+(error?'offline':'')}/>{updated?'Admin API 연결됨':'연결 중'}</span></header><section className="content"><div className="heading"><div><p className="eyebrow">{titles[page][0]}</p><h1>{titles[page][1]}</h1><p className="subtitle">{page==='policies'?'생성된 인가 정책을 검토하고 적용 상태를 관리하세요.':page==='logs'?'모든 요청의 인가 판단을 확인하세요. 5초마다 자동으로 갱신됩니다.':page==='settings'?'알림 채널과 발송 기준을 관리하세요.':'자동 판단을 보류한 정책을 검토하고 인가 기준을 명확히 하세요.'}</p></div><button onClick={refresh}>↻ 새로고침</button></div>
    {page==='policies'&&<div className="stats">{[['전체 정책',policies.length,'등록된 인가 규칙'],['활성 정책',policies.filter(p=>p.status==='ACTIVE').length,'프록시에 적용 중'],['차단 요청',logs.filter(l=>l.verdict==='BLOCK').length,'최근 100건 기준'],['검토 필요',reviews.length,'manual_review_required']].map(([name,value,note])=><article key={name}><span>{name}</span><strong>{value.toString().padStart(2,'0')}</strong><small>{note}</small></article>)}</div>}
    {features.observability&&page==='policies'&&<Observability api={api}/>}
    {error&&<div role="alert" className="error">{error}</div>}{notice&&<div role="status" className="notice">{notice}</div>}
    <div className="panel"><div className="panelhead"><h2>{titles[page][1]} <span>{page==='settings'?'':page==='policies'?visible.length:page==='review'?reviews.length:logs.length}</span></h2>{page==='policies'?<select aria-label="정책 상태 필터" value={filter} onChange={e=>setFilter(e.target.value)}>{['ALL','PENDING','ACTIVE','REJECTED'].map(s=><option key={s}>{s}</option>)}</select>:page==='logs'?<select aria-label="verdict 필터" value={verdict} onChange={e=>setVerdict(e.target.value)}>{['ALL','PASS','BLOCK','OBSERVE',...(features.mode?['would_block']:[])].map(s=><option key={s}>{s}</option>)}</select>:page==='review'?<small>OBSERVE 수: 최근 100건 기준</small>:null}</div>
    {page==='policies'&&<div className="scroll"><table><thead><tr><th>엔드포인트 / 정책</th><th>인가 패턴</th><th>신뢰도</th><th>상태</th>{features.mode&&<th>모드 / 버전</th>}<th>관리</th></tr></thead><tbody>{visible.map(p=><tr key={p.id}><td><div className="endpoint"><b>{p.endpoint.method}</b> {p.endpoint.path}</div><small>{p.id}</small></td><td>{p.label}</td><td>{Math.round(p.confidence*100)}%</td><td>{badge(p.status)}</td>{features.mode&&<td>{badge(p.mode)}<small>v{p.version} · {p.source}</small></td>}<td>{controls(p)}</td></tr>)}</tbody></table>{!visible.length&&<p className="empty">표시할 정책이 없습니다.</p>}</div>}
    {page==='logs'&&<div className="scroll"><table><thead><tr><th>시간 / 요청 ID</th><th>호출자</th><th>요청</th><th>판단</th><th>정책 / 사유</th>{features.explain&&<th>설명</th>}</tr></thead><tbody>{logs.filter(l=>verdict==='ALL'||(verdict==='would_block'?l.would_block:l.verdict===verdict)).map(l=><tr key={l.request_id}><td>{time(l.ts)}<small>{l.request_id}</small></td><td>{l.sub||'익명'}</td><td>{l.method} {l.path}</td><td>{badge(l.verdict)}{features.mode&&<small>{l.mode}{l.would_block?' · would_block':''}</small>}</td><td>{l.policy_id||'매칭 정책 없음'}<small>{l.reason}</small></td>{features.explain&&<td className="explanation">{l.explanation||'—'}</td>}</tr>)}</tbody></table>{!logs.filter(l=>verdict==='ALL'||(verdict==='would_block'?l.would_block:l.verdict===verdict)).length&&<p className="empty">표시할 탐지 로그가 없습니다.</p>}</div>}
    {page==='settings'&&<AlertSettings/>}{page==='review'&&<div className="reviews">{reviews.map(p=><article key={p.id}><div><div className="endpoint"><b>{p.endpoint.method}</b> {p.endpoint.path}</div><small>{p.id}</small><p>{p.evidence}</p>{badge(p.status)}</div><div className="reviewright"><strong>{logs.filter(l=>l.policy_id===p.id&&l.verdict==='OBSERVE').length}<small>OBSERVE · 최근 100건</small></strong>{controls(p)}</div></article>)}{!reviews.length&&<p className="empty">검토 대기 정책이 없습니다.</p>}</div>}
    <div className="panelbottom">{updated?`마지막 갱신 ${updated.toLocaleTimeString('ko-KR')}`:'데이터를 불러오는 중…'}<span>5초 자동 갱신</span></div></div><p className="footnote">승인된 ACTIVE 정책만 프록시에 적용됩니다. 변경 사항은 정책 갱신 주기 내에 반영됩니다.</p></section></main>
    {edit&&<div className="overlay"><section role="dialog" aria-modal="true" aria-label="정책 YAML 편집" className="editor"><div className="panelhead"><h2>정책 YAML</h2><button onClick={()=>setEdit(null)} aria-label="닫기">✕</button></div><div className="editortabs">{features.rag&&<button className={tab==='cve'?'primary':''} onClick={()=>setTab('cve')}>근거 CVE</button>}<button className={tab==='yaml'?'primary':''} onClick={()=>setTab('yaml')}>YAML</button>{features.reanalysis&&<button className={tab==='proposals'?'primary':''} onClick={()=>setTab('proposals')}>제안</button>}</div>{tab==='cve'?<Evidence policy={edit} api={api}/>:tab==='proposals'?<Proposals policy={edit} api={api} onChanged={async()=>{const current=await api('/policies/'+encodeURIComponent(edit.id));setEdit(current);setYaml(stringify(current));await refresh();}}/>:<><p>id · created_at · status는 유지하세요. 상태는 목록의 전이 버튼으로 변경합니다.</p>{error&&<div role="alert" className="error">{error}</div>}<textarea aria-label="정책 YAML" spellCheck="false" value={yaml} onChange={e=>setYaml(e.target.value)}/><div className="editorbuttons"><button onClick={()=>setEdit(null)}>취소</button><button className="primary" disabled={busy} onClick={save}>YAML 저장</button></div></>}</section></div>}
  </div>;
}
createRoot(document.getElementById('root')).render(<App/>);
