export PATH="/c/BLADE/.python:/c/BLADE/.python/Scripts:$PATH"
mkdir -p /c/BLADE/verification/demo_v7_runtime && cd /c/BLADE/verification/demo_v7_runtime
set -a; source /c/BLADE/.env; set +a
export PYTHONPATH=/c/BLADE
export BLADE_CLASSIFIER=lora
export BLADE_LORA_MODEL=blade-qwen-lora-v7
export BLADE_LORA_MIN_CONFIDENCE=0.9
export BLADE_LLM_PROVIDER=ollama          # 빠지면 roles 추출 실패 → 반드시 넣는다
export BLADE_LLM_MODEL=qwen2.5:7b
export BLADE_OLLAMA_URL=http://127.0.0.1:11434
export BLADE_TARGET_URL=http://127.0.0.1:9000
export BLADE_ADMIN_URL=http://127.0.0.1:8100
export BLADE_DB_DSN="sqlite:///file:C:/BLADE/verification/demo_v7_runtime/demo.db?mode=ro&uri=true"
export BLADE_FAIL_MODE=closed
export BLADE_POLICY_POLL_SEC=5
export BLADE_PHASE2_ENABLED=false
