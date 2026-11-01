#!/usr/bin/env bash
# Packs finished runs under <BASE>/runs into <BASE>/export for download to a local machine:
#   <EXPORT_NAME>_results.tar.gz  - per run: config*.json, env*.json, eval*/ (predictions; *_smoke dirs excluded), logs/ (+ run_all*.log, SUMMARY.tsv)
#   <EXPORT_NAME>_adapters.tar.gz - per run: adapter/ (final LoRA adapter); skipped when EXPORT_ADAPTERS=0 (evaluation-only re-runs, adapters unchanged)
# EXPORT_NAME defaults to blade_v4 (LoRA v4 experiment); run_all.sh sets blade_<decoding> for DECODING!=default (task B: blade_stable).
# checkpoints/ are left out (intermediate states for resuming only). Re-run any time; it overwrites the previous export of the same name.
set -euo pipefail
BASE=${BASE:-/workspace/blade_lora_v3}
NAME=${EXPORT_NAME:-blade_v4}
EXPORT_ADAPTERS=${EXPORT_ADAPTERS:-1}
OUT="$BASE/export"
mkdir -p "$OUT"
cd "$BASE/runs"
runs=$(ls -d lora_*/ base_*/ 2>/dev/null | tr -d / || true)

{
  printf 'run\tlog\tsteps\tminutes\ttrain_loss\toas_rows\toas_parse_err\toas_code_rows\toas_code_parse_err\tsupp_oas_parse_err\tsupp_oas_code_parse_err\tv5test_oas_parse_err\tv5test_oas_code_parse_err\tstatus\n'
  for r in $runs; do
    python3 - "$r" <<'EOF'
import json, re, sys, pathlib
r = sys.argv[1]; d = pathlib.Path(r)
tr = d / "logs/train_result.json"
t = json.loads(tr.read_text()) if tr.exists() else {}
loss = t.get("train_loss")
for lp in sorted(d.glob("logs/run*.log")):   # run.log = default decoding (as exported for LoRA v4), run_<decoding>.log = re-evaluations
    log = lp.read_text(errors="replace")
    ev = {}
    for m in re.finditer(r"(?<!\[SMOKE\])\n[^\n]*? (supp |v5test )?(oas_code|oas): (\d+) rows, parse errors (\d+)[^\n]*$", "\n" + log, re.M):
        if "[SMOKE]" in m.group(0): continue
        ev[(m.group(1) or "") + m.group(2)] = (m.group(3), m.group(4))
    done = "done" if re.search(r"INFO done ", log) else "incomplete"
    print("\t".join(map(str, [r, lp.name, t.get("steps", ""), t.get("minutes", ""), f"{loss:.4f}" if loss else "",
          *ev.get("oas", ("", "")), *ev.get("oas_code", ("", "")), ev.get("supp oas", ("", ""))[1], ev.get("supp oas_code", ("", ""))[1],
          ev.get("v5test oas", ("", ""))[1], ev.get("v5test oas_code", ("", ""))[1], done])))
EOF
  done
} > "$OUT/SUMMARY.tsv"

tar czf "$OUT/${NAME}_results.tar.gz" --exclude='*_smoke' -C "$BASE/runs" $(ls run_all*.log) \
  $(for r in $runs; do ls -d $r/config*.json $r/env*.json $r/eval* $r/logs 2>/dev/null; done) -C "$OUT" SUMMARY.tsv $(cd "$OUT" && ls gguf/*.json gguf/*.log gguf/SHA256SUMS* 2>/dev/null) || [ $? -eq 1 ]  # 1 = a log was still being written; gguf/: manifests only (the GGUF itself stays in export/gguf/)
files="${NAME}_results.tar.gz"
if [ "$EXPORT_ADAPTERS" = "1" ]; then
  tar czf "$OUT/${NAME}_adapters.tar.gz" -C "$BASE/runs" $(for r in $runs; do [ -f "$r/adapter/adapter_model.safetensors" ] && echo "$r/adapter"; done)
  files="$files ${NAME}_adapters.tar.gz"
fi
(cd "$OUT" && sha256sum $files > "SHA256SUMS_${NAME}")
cat "$OUT/SUMMARY.tsv"
ls -lh "$OUT"
