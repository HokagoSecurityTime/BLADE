# 재부팅 후 Docker 서버 켜기

기존 정책·탐지 로그를 유지하며 Docker 서비스를 다시 실행하는 안내다. 로컬 Python 서버 실행 명령은 사용하지 않는다.
아래 명령은 **PowerShell** 기준이며, 이 문서를 작성하면서 서버를 직접 기동하거나 데이터를 변경하지는 않았다.

## 1. Docker Desktop 실행

시작 메뉴에서 **Docker Desktop**을 실행하거나 다음 명령을 사용한다.

```powershell
Set-Location C:\BLADE
Start-Process -FilePath 'C:\Program Files\Docker\Docker\Docker Desktop.exe' -WindowStyle Hidden
$env:PATH = 'C:\Program Files\Docker\Docker\resources\bin;' + $env:PATH
```

엔진이 준비될 때까지 잠시 기다린 뒤 확인한다.

```powershell
docker info
```

Server 정보가 나오면 준비 완료다. `failed to connect` 또는 named pipe 오류가 나오면 Docker Desktop의 실행 상태를 확인하고 잠시 후 다시 실행한다.

## 2. 이전에 사용한 프로젝트명 확인

```powershell
docker compose ls -a
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

이전에 실제 통합 검증에 사용한 프로젝트명은 **blade-verify-20260910**이다.
재촬영 때 별도로 만든 **blade-recording-01** 등이 있다면, 그때 사용한 이름을 선택해야 해당 정책·DB가 다시 열린다.
같은 포트를 사용하는 프로젝트 두 개를 동시에 시작하면 안 된다.

이후 명령에서 사용할 프로젝트명을 한 번 지정한다.

```powershell
$bladeProject = 'blade-verify-20260910'
```

재촬영 프로젝트를 다시 켜려는 경우에는 위 값을 실제 사용한 프로젝트명으로 바꾼다.
**새 이름을 임의로 사용하면 기존 데이터가 아닌 새 볼륨을 사용하게 된다.**

## 3. 컨테이너 전체 기동

```powershell
docker compose -p $bladeProject up -d
docker compose -p $bladeProject ps
```

재부팅 후 단순 재기동에는 `--build`가 필요하지 않다. 기존 볼륨의 데이터는 유지된다.

| 서비스 | 주소 / 역할 | 정상 상태 |
|---|---|---|
| demo-backend | http://localhost:9000 | healthy |
| admin-api | http://localhost:8100 | healthy |
| proxy | http://localhost:8080 | healthy |
| dashboard | **http://localhost:3000** | healthy |
| alerts | 별도 알림 워커, 공개 포트 없음 | Up / running |

alerts에는 healthcheck가 없으므로 healthy 표시가 없어도 된다. Webhook이 비어 있으면 외부 알림을 전송하지 않는다.

### 포트 사용 중 오류가 나면

```powershell
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object LocalPort -in 3000,8080,8100,9000 |
    Select-Object LocalAddress,LocalPort,OwningProcess
```

다른 Docker 프로젝트가 사용 중이면 해당 프로젝트만 중지한다. 예:

```powershell
docker compose -p blade-recording-01 stop
```

로컬 Python 서비스가 포트를 사용 중이면 실행 명령을 먼저 확인하고 해당 프로세스만 중지한다.
재부팅 전 `presentation-processes.json`의 PID를 그대로 믿고 종료하면 안 된다. PID는 다른 프로그램에 재사용될 수 있다.

## 4. 접속 및 정책 상태 확인

PowerShell에서는 `curl` 별칭 대신 **curl.exe**를 사용한다.

```powershell
curl.exe -i http://localhost:9000/public/health
curl.exe -i http://localhost:8080/public/health
curl.exe -i 'http://localhost:8100/policies?status=ACTIVE'
Start-Process 'http://localhost:3000'
```

health 요청은 200이 기대된다. 대시보드에서 기존 정책 목록을 확인한다.
타인 주문 조회·삭제를 차단하려면 아래 정책이 `owner_match`, `ACTIVE`인지 확인한다.

- `pol_orders_get_by_orderId`
- `pol_orders_delete_by_orderId`

PENDING이라면 대시보드에서 승인하고 정책 갱신 주기(기본 5초)만큼 기다린다.
서버를 다시 켜기 위해 `/generate`를 다시 호출할 필요는 없다. 이미 정책이 있으면 중복 생성이나 재승인은 409가 날 수 있다.

**데이터 구분:** Docker 볼륨의 정책·로그와 `verification/presentation-runtime/`의 로컬 검증 DB는 별개다.
Docker 대시보드에 로컬 검증 결과가 자동으로 복사되지는 않는다.

## 5. 토큰 재발급 및 요청 테스트

COMMANDS.md의 고정 토큰은 만료될 수 있으므로 새로 발급한다. 아래 변수는 현재 PowerShell 창에서만 유지된다.

```powershell
$TOKEN99 = (docker compose -p $bladeProject exec -T proxy python -m proxy.mktoken user_99 --expires-in 86400).Trim()
$TOKEN77 = (docker compose -p $bladeProject exec -T proxy python -m proxy.mktoken user_77 --expires-in 86400).Trim()

# 타인 조회: 주문 정책 ACTIVE이면 403
curl.exe -i -H "Authorization: Bearer $TOKEN99" http://localhost:8080/orders/1042

# 소유자 조회: 200
curl.exe -i -H "Authorization: Bearer $TOKEN77" http://localhost:8080/orders/1042
```

기존 JWT 시크릿 길이 경고가 출력될 수 있다. 이 안내에서는 시크릿이나 코드를 변경하지 않는다.

## 6. LLM으로 정책을 새로 생성할 경우에만: Ollama

**기존 ACTIVE 정책으로 차단 시연만 할 때는 Ollama가 필요 없다.**
`/generate`로 새 정책을 만들 때 `.env`가 Ollama를 선택했다면, 호스트 PC의 Ollama가 실행 중이어야 한다.

이미 실행 중인지 확인한다.

```powershell
curl.exe -i http://localhost:11434/api/tags
```

실행되지 않았다면 별도 PowerShell 창에서 다음을 실행하고 창을 유지한다.

```powershell
Set-Location C:\BLADE
$env:OLLAMA_HOST = '0.0.0.0:11434'
& 'C:\BLADE\.ollama\ollama.exe' serve
```

기존 Ollama가 이미 11434 포트를 사용하면 중복 실행하지 않는다.
컨테이너에서 연결 가능한지도 확인한다.

```powershell
docker compose -p $bladeProject exec -T admin-api python -c "import os,httpx; r=httpx.get(os.environ['BLADE_OLLAMA_URL']+'/api/tags',timeout=10); r.raise_for_status(); print([m['name'] for m in r.json()['models']])"
```

`.env`의 BLADE_LLM_MODEL에 설정한 모델명이 출력되는지 확인한다.

## 7. 로그 보기·중지

```powershell
docker compose -p $bladeProject logs --tail 50 demo-backend admin-api proxy dashboard alerts

# 실시간 로그: Ctrl+C는 로그 보기만 종료하고 서버는 계속 실행된다.
docker compose -p $bladeProject logs -f proxy admin-api

# 시연 종료 후 서비스 중지, 데이터 유지
docker compose -p $bladeProject stop
```

Docker 서비스 로그는 `docker compose logs`로 확인한다.
`verification/logs/demo_backend.log` 등은 이전 로컬 프로세스의 로그이므로 Docker 재기동 후 새 요청이 그 파일에 추가되는 것은 아니다.
기존 데이터를 유지하려면 `docker compose down -v`나 볼륨 삭제 명령을 실행하지 않는다.

## 빠른 실행 요약

Docker Desktop이 준비된 뒤, PowerShell에서:

```powershell
Set-Location C:\BLADE
$env:PATH = 'C:\Program Files\Docker\Docker\resources\bin;' + $env:PATH
$bladeProject = 'blade-verify-20260910'  # 실제 사용했던 프로젝트명
docker compose -p $bladeProject up -d
docker compose -p $bladeProject ps
Start-Process 'http://localhost:3000'
```
