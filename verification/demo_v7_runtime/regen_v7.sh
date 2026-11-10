#!/bin/bash
# 2.3: regenerate the 7 demo policies with blade-qwen-lora-v7 (same inputs as the v5 demo: openapi_clean.json + demo_backend schema/main),
# approve them all, and leave the YAMLs in ./policies (admin_api store writes them). v5 generated set stays untouched in demo_v5_runtime/.
source /c/BLADE/verification/demo_v7_runtime/env.sh
cd /c/BLADE/verification/demo_v7_runtime
LOG=/c/BLADE/verification/demo_v7_runtime/regen.log
echo "admin start $(date -u +%FT%TZ) model=$BLADE_LORA_MODEL min_conf=$BLADE_LORA_MIN_CONFIDENCE" | tee -a "$LOG"
python -m uvicorn admin_api.main:app --host 127.0.0.1 --port 8100 > admin_8100.log 2>&1 &
echo $! > admin_8100.pid
for i in $(seq 1 60); do curl -s -o /dev/null http://127.0.0.1:8100/policies && break; sleep 1; done
echo "generate start $(date -u +%FT%TZ)" | tee -a "$LOG"
START=$(date +%s)
curl -s --max-time 1800 -X POST http://127.0.0.1:8100/generate \
  -F oas=@openapi_clean.json -F erd=@/c/BLADE/demo_backend/schema.sql -F controller=@/c/BLADE/demo_backend/main.py \
  -o generate_response.json -w "http %{http_code}\n" | tee -a "$LOG"
echo "generate end $(date -u +%FT%TZ) elapsed $(( $(date +%s) - START ))s" | tee -a "$LOG"
for id in $(curl -s http://127.0.0.1:8100/policies | python -X utf8 -c "import json,sys;print(' '.join(p['id'] for p in json.load(sys.stdin)))"); do
  curl -s -o /dev/null -w "approve $id %{http_code}\n" -X POST http://127.0.0.1:8100/policies/$id/approve | tee -a "$LOG"
done
curl -s http://127.0.0.1:8100/policies | python -X utf8 -c "
import json,sys
for p in json.load(sys.stdin): print(p['id'], p['label'], p['confidence'], p['status'], p['params'].get('roles'), (p['params'].get('owner_lookup') or {}))" | tee -a "$LOG"
echo "done $(date -u +%FT%TZ)" | tee -a "$LOG"
