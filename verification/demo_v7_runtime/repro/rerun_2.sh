#!/bin/bash
# Reproducibility re-run (user request 2026-11-10 #2): regenerate only the 2 policies whose v7 label differed from v5
# (GET /admin/reports, GET /orders/{orderId}) with the same ERD/controller and the same OAS entries (subset file), fresh store, admin 8103.
source /c/BLADE/verification/demo_v7_runtime/env.sh
cd /c/BLADE/verification/demo_v7_runtime/repro
LOG=/c/BLADE/verification/demo_v7_runtime/repro/rerun_2.log
echo "admin start $(date -u +%FT%TZ) model=$BLADE_LORA_MODEL" | tee -a "$LOG"
python -m uvicorn admin_api.main:app --host 127.0.0.1 --port 8103 > admin_8103.log 2>&1 &
PID=$!
for i in $(seq 1 60); do curl -s -o /dev/null http://127.0.0.1:8103/policies && break; sleep 1; done
START=$(date +%s)
curl -s --max-time 1800 -X POST http://127.0.0.1:8103/generate -F oas=@openapi_clean_2.json -F erd=@/c/BLADE/demo_backend/schema.sql -F controller=@/c/BLADE/demo_backend/main.py -o generate_response.json -w "http %{http_code}\n" | tee -a "$LOG"
echo "generate end $(date -u +%FT%TZ) elapsed $(( $(date +%s) - START ))s" | tee -a "$LOG"
python -X utf8 -c "
import json,yaml
for p in json.load(open('generate_response.json',encoding='utf-8')):
    first=yaml.safe_load(open('../policies/'+p['id']+'.yaml',encoding='utf-8'))
    print(p['id'], 'first', first['label'], '| rerun', p['label'], p['confidence'], 'MATCH' if first['label']==p['label'] else 'DIFF', '|', p['evidence'][:160])" | tee -a "$LOG"
kill $PID 2>/dev/null; echo "done $(date -u +%FT%TZ)" | tee -a "$LOG"
