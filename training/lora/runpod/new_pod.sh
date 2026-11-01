#!/usr/bin/env bash
# Prepares a FRESH RunPod pod (no network volume) for task B (stable-decoding re-evaluation) and runs the smoke test.
# Usage, after uploading the two files to /workspace and extracting the bundle:
#     cd /workspace && mkdir -p blade_lora_v3 && tar -xzf blade_lora_stable_runpod_*.tgz -C blade_lora_v3
#     bash /workspace/blade_lora_v3/runpod/new_pod.sh /workspace/blade_v4_adapters.tar.gz
# Steps: verify the adapter archive hash -> extract the 12 final adapters into runs/ -> setup.sh (unsloth, lm-format-enforcer) -> smoke test (8 rows, base + v4 s42)
# -> print the launch command. It never trains and never deletes anything. run_all.sh stops the pod automatically when everything has ended (STOP_POD=1 default).
# /workspace (pod volume disk or network volume) survives a stop, so export/ can be downloaded after restarting the pod; it is lost only if the pod is TERMINATED.
set -euo pipefail
BASE=${BASE:-/workspace/blade_lora_v3}
ADAPTERS=${1:-/workspace/blade_v4_adapters.tar.gz}
ADAPTERS_SHA=a3ce55a40554e8ad08dcc1217090bd6202b95a35616765906daf0445af181053   # blade_v4_adapters.tar.gz exported from the 2026-10-27 run (12 adapters incl. v2/v3a/v3b/v4)
export HF_HOME=${HF_HOME:-/workspace/hf}
cd "$BASE"
echo "== 1/5 adapter archive"
[ -f "$ADAPTERS" ] || { echo "adapter archive not found: $ADAPTERS"; exit 1; }
got=$(sha256sum "$ADAPTERS" | cut -d' ' -f1)
[ "$got" = "$ADAPTERS_SHA" ] || { echo "adapter archive hash mismatch: $got (expected $ADAPTERS_SHA). Re-upload it."; exit 1; }
mkdir -p runs && tar -xzf "$ADAPTERS" -C runs
n=$(ls runs/*/adapter/adapter_model.safetensors | wc -l); echo "adapters extracted: $n"
for r in lora_v2_s42_runpod lora_v2_s43_runpod lora_v2_s44_runpod lora_v3b_s42 lora_v3b_s43 lora_v3b_s44 lora_v4_s42 lora_v4_s43 lora_v4_s44; do
  [ -f "runs/$r/adapter/adapter_model.safetensors" ] || { echo "missing adapter: $r"; exit 1; }
done
echo "== 2/5 data manifests"
sha256sum data_v2/data_v2_hashes.json data_v3/data_v3_hashes.json data_v4/data_v4_hashes.json   # run_train.py asserts these against DATASETS[...]['sha']
echo "== 3/5 environment (setup.sh)"
bash runpod/setup.sh
command -v runpodctl >/dev/null && echo "runpodctl ok, POD_ID=${RUNPOD_POD_ID:-?}" || echo "runpodctl missing: stop the pod manually from the console when done"
df -h /workspace | tail -1
echo "== 4/5 smoke test (8 rows per job, base + v4 s42, not scored)"
python runpod/run_train.py --data base --seed 0 --eval-only --decoding stable --limit 8 --base "$BASE"
python runpod/run_train.py --data v4 --seed 42 --eval-only --decoding stable --limit 8 --base "$BASE"
echo "---- smoke summary (all 8 rows should parse: 'parse errors 0'; compare 'mean ms/row' with the old run, ~1000-2000 ms/row on A100)"
grep -h "SMOKE" runs/base_qwen_runpod/logs/run_stable.log runs/lora_v4_s42/logs/run_stable.log
python3 - <<'PY'
import json, glob
for p in sorted(glob.glob('runs/lora_v4_s42/eval_stable_smoke/*.jsonl')):
    rows = [json.loads(l) for l in open(p, encoding='utf-8')]
    print(p.split('/')[-1], 'parsed', sum(r['prediction'] is not None for r in rows), '/', len(rows), 'labels', [r['prediction']['label'] if r['prediction'] else None for r in rows])
PY
echo "== 5/5 ready. Launch the full run (10 models, ~3-5 h on A100, longer on smaller GPUs; the pod stops itself at the end) with:"
echo "    tmux new -d -s blade \"DECODING=stable bash $BASE/runpod/run_all.sh\""
echo "    tail -f $BASE/runs/run_all_stable.log"
echo "Results: $BASE/export/blade_stable_results.tar.gz + SHA256SUMS_blade_stable, kept on /workspace across the stop. Do NOT terminate the pod before downloading them."
