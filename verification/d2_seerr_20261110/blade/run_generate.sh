#!/bin/bash
# Generate policies for the 10 Seerr endpoints with the LoRA classifier set in env.sh (labels are the model's; no human label).
set -u
ROOT=/c/BLADE/verification/d2_seerr_20261110
cd "$ROOT/blade" && source "$ROOT/blade/env.sh"
echo "generate start $(date -u +%FT%TZ) model=$BLADE_LORA_MODEL min_conf=$BLADE_LORA_MIN_CONFIDENCE" | tee -a "$ROOT/logs/timeline.log"
START=$(date +%s)
curl -s --max-time 3600 -X POST http://127.0.0.1:8102/generate \
  -F oas=@"$ROOT/inputs/openapi_seerr_subset.json" \
  -F erd=@"$ROOT/inputs/schema_seerr.sql" \
  -F controller=@"$ROOT/inputs/controller_seerr_flat.ts" \
  -o "$ROOT/blade/generate_response.json" -w "http %{http_code}\n"
echo "generate end $(date -u +%FT%TZ) elapsed $(( $(date +%s) - START ))s" | tee -a "$ROOT/logs/timeline.log"
python -X utf8 -c "
import json; d=json.load(open('$ROOT/blade/generate_response.json',encoding='utf-8'))
for p in d: print(p['endpoint']['method'], p['endpoint']['path'], '->', p['label'], p.get('confidence'), p['params'].get('object_param'), (p['params'].get('owner_lookup') or {}), p['params'].get('roles'))"
