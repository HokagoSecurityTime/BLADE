from pathlib import Path
p=Path('dashboard/src/main.jsx');s=p.read_text(encoding='utf-8')
s=s.replace("page==='logs'?'모든 요청의 인가 판단을 확인하세요. 5초마다 자동으로 갱신됩니다.':'자동 판단", "page==='logs'?'모든 요청의 인가 판단을 확인하세요. 5초마다 자동으로 갱신됩니다.':page==='settings'?'알림 채널과 발송 기준을 관리하세요.':'자동 판단")
s=s.replace("page==='policies'?visible.length:page==='review'?reviews.length:logs.length", "page==='settings'?'':page==='policies'?visible.length:page==='review'?reviews.length:logs.length")
s=s.replace(':<small>OBSERVE 수: 최근 100건 기준</small>', ":page==='review'?<small>OBSERVE 수: 최근 100건 기준</small>:null")
p.write_text(s,encoding='utf-8')
