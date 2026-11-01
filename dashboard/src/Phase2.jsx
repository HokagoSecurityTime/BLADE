import React, {useEffect, useState} from 'react';
import {stringify} from 'yaml';

export function Evidence({policy,api}) {
  const [refs,setRefs]=useState([]),[error,setError]=useState('');
  useEffect(()=>{api('/evidence/'+encodeURIComponent(policy.id)).then(setRefs).catch(e=>setError(e.message));},[policy.id]);
  const cves=refs.filter(r=>r.kind==='cve');
  return <section className="proposals"><h3>근거 CVE</h3><p>분류 시 실제 인용한 참고 자료입니다. 해당 서비스에서 취약점이 확인되었다는 의미는 아닙니다.</p>{error&&<p role="alert">{error}</p>}{cves.map(r=><article key={r.ref}><b>{r.ref}</b><pre style={{whiteSpace:'pre-wrap'}}>{r.snippet}</pre></article>)}{!cves.length&&<p className="empty">인용한 CVE 근거가 없습니다.</p>}</section>;
}

// Sequence alignment, preserving inserted/deleted lines rather than comparing
// unrelated line numbers. YAML is rendered as text, never interpreted as HTML.
export function alignDiff(before, after) {
  const a=before.trimEnd().split('\n'), b=after.trimEnd().split('\n');
  const dp=Array.from({length:a.length+1},()=>new Uint32Array(b.length+1));
  for(let i=a.length-1;i>=0;i--)for(let j=b.length-1;j>=0;j--)dp[i][j]=a[i]===b[j]?1+dp[i+1][j+1]:Math.max(dp[i+1][j],dp[i][j+1]);
  const rows=[];let i=0,j=0;
  while(i<a.length||j<b.length){
    if(i<a.length&&j<b.length&&a[i]===b[j])rows.push({left:a[i++],right:b[j++],kind:'same'});
    else if(i<a.length&&(j===b.length||dp[i+1][j]>=dp[i][j+1]))rows.push({left:a[i++],right:'',kind:'removed'});
    else rows.push({left:'',right:b[j++],kind:'added'});
  }
  return rows;
}

export function Proposals({policy, api, onChanged}) {
  const [items,setItems]=useState([]),[selected,setSelected]=useState(null),[current,setCurrent]=useState(policy);
  const [message,setMessage]=useState(''),[busy,setBusy]=useState(false);
  async function refresh(){try{const [p,rows]=await Promise.all([api('/policies/'+encodeURIComponent(policy.id)),api('/policies/'+encodeURIComponent(policy.id)+'/proposals')]);setCurrent(p);setItems(rows);setSelected(prev=>rows.find(x=>x.id===prev?.id)||rows[0]||null);}catch(e){setMessage(e.message);}}
  useEffect(()=>{refresh();const timer=setInterval(refresh,5000);return ()=>clearInterval(timer);},[policy.id]);
  async function action(verb){setBusy(true);try{await api(`/proposals/${selected.id}/${verb}`,{method:'POST'});setMessage(verb==='accept'?'제안을 반영했습니다. observe 모드로 전환되었습니다.':'제안을 기각했습니다.');await refresh();await onChanged();}catch(e){setMessage(e.message);}finally{setBusy(false);}}
  return <section className="proposals"><h3>재분석 제안</h3><p>원본은 수락 전까지 변경되지 않습니다. 수정된 원본에 대한 오래된 제안은 다시 검토해야 합니다.</p>{message&&<p role="status">{message}</p>}
    {!!items.length&&<select aria-label="재분석 제안 선택" value={selected?.id||''} onChange={e=>setSelected(items.find(p=>String(p.id)===e.target.value))}>{items.map(p=><option key={p.id} value={p.id}>#{p.id} · {p.status} · {p.reason}</option>)}</select>}
    {selected?<><p><b>사유</b> {selected.reason}</p><p>{selected.diff_summary}</p><div className="yamldiff"><div className="diffheaders"><b>현재 정책 · v{current.version}</b><b>제안 · 기준 v{selected.base_version}</b></div>{alignDiff(stringify(current),selected.proposed_yaml).map((row,i)=><div className={'diffrow '+row.kind} key={i}><pre>{row.left||' '}</pre><pre>{row.right||' '}</pre></div>)}</div>{selected.status==='PENDING'&&<div className="actions"><button className="primary" disabled={busy} onClick={()=>action('accept')}>제안 수락</button><button disabled={busy} onClick={()=>action('dismiss')}>제안 기각</button></div>}</>:<p className="empty">대기 중인 재분석 제안이 없습니다.</p>}
  </section>;
}

export function Observability({api}) {
  const [value,setValue]=useState(null),[error,setError]=useState('');
  useEffect(()=>{let live=true;async function refresh(){try{const result=await api('/metrics/observability');if(live){setValue(result);setError('');}}catch(e){if(live)setError(e.message);}}refresh();const timer=setInterval(refresh,5000);return ()=>{live=false;clearInterval(timer);};},[]);
  return <div className="observability"><b>관측률 · 최근 60초</b>{error?<span role="status">지표를 가져올 수 없습니다.</span>:value?<><strong>{(value.rate*100).toFixed(1)}%</strong><span>전체 {value.total} · 정책 매칭 {value.with_policy} · 조회 성공 {value.lookup_ok}</span></>:<span>불러오는 중…</span>}</div>;
}
