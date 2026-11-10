# BLADE stack for the Seerr v3.5.1 real-service run (D2, 2026-11-10). Separate from the demo stack (127.0.0.1:8080/8100/9000)
# and from the Mealie stack (127.0.0.2:8080 / 8101 / 9926), which are left untouched.
export PATH="/c/BLADE/.python:/c/BLADE/.python/Scripts:$PATH"
set -a; source /c/BLADE/.env; set +a          # BLADE_JWT_SECRET, Ollama/LLM settings; overrides below
export PYTHONPATH=/c/BLADE
export BLADE_CLASSIFIER=lora
export BLADE_LORA_MODEL=${BLADE_LORA_MODEL:-blade-qwen-lora-v7}       # D2 policy labels come from LoRA v7 (set after D1 registration)
export BLADE_LORA_MIN_CONFIDENCE=${BLADE_LORA_MIN_CONFIDENCE:-0.9}    # replaced by threshold_val_v7.json once D1 decides it
export BLADE_LLM_PROVIDER=ollama
export BLADE_LLM_MODEL=qwen2.5:7b                                     # roles / parameter extraction (unchanged pipeline)
export BLADE_OLLAMA_URL=http://127.0.0.1:11434
export BLADE_TARGET_URL=http://127.0.0.1:5056          # token shim -> Seerr 5055
export BLADE_ADMIN_URL=http://127.0.0.1:8102
export BLADE_PROXY_HOST=127.0.0.3                      # proxy port is fixed at 8080; 127.0.0.1 (demo) and 127.0.0.2 (Mealie) are taken
export BLADE_DB_DSN="sqlite:///file:C:/BLADE/verification/d2_seerr_20261110/snapshot/db.sqlite3?mode=ro&uri=true"
export BLADE_FAIL_MODE=closed
export BLADE_POLICY_POLL_SEC=5
export BLADE_PHASE2_ENABLED=false
export SEERR_URL=http://127.0.0.1:5055
export SEERR_API_KEY=testkey                           # settings.main.apiKey from cypress/config/settings.cypress.json (verbatim seed)
export SHIM_PORT=5056
