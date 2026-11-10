#!/bin/bash
# Start the BLADE admin API for the Seerr run (8102, cwd = this folder -> blade.db / policies/ / detections.jsonl here).
ROOT=/c/BLADE/verification/d2_seerr_20261110
cd "$ROOT/blade" && source "$ROOT/blade/env.sh"
python -m uvicorn admin_api.main:app --host 127.0.0.1 --port 8102 > "$ROOT/blade/admin_8102.log" 2>&1 &
echo $! > "$ROOT/blade/admin_8102.pid"
for i in $(seq 1 60); do curl -s --max-time 2 http://127.0.0.1:8102/policies > /dev/null && break; sleep 1; done
echo "admin 8102 up (pid $(cat "$ROOT/blade/admin_8102.pid")) model=$BLADE_LORA_MODEL min_conf=$BLADE_LORA_MIN_CONFIDENCE"
