#!/usr/bin/env bash
# C-5 (AGENTS.md 작업 C): one-time setup on a fresh RunPod pod for GGUF conversion + Ollama equivalence/val inference. No training.
# Needs: PyTorch 2.x / CUDA template, >= 64 GB RAM (fp32 merge of a 7.6B model), container disk >= 80 GB (HF cache 15 GB + merged 15 GB + f16 15 GB, deleted as it goes).
# Run this FIRST after every pod start (pip packages and Ollama live in the container, not on the volume).
set -euo pipefail
LOCAL=${C5_LOCAL:-/root/c5}                 # container disk: HF cache, merge work dir, llama.cpp build, Ollama models
mkdir -p "$LOCAL"
export HF_HOME=${HF_HOME:-$LOCAL/hf}
pip install -q transformers peft safetensors sentencepiece httpx cmake
# A template torchaudio pinned to an older torch breaks `import transformers` (libtorchaudio.so undefined symbol); nothing here uses audio.
python - <<'PY' || pip uninstall -y -q torchaudio
import torch, torchaudio
PY
command -v tmux >/dev/null || (apt-get update -qq && apt-get install -y -qq tmux)
command -v cmake >/dev/null || (apt-get update -qq && apt-get install -y -qq cmake)
if ! command -v ollama >/dev/null; then curl -fsSL https://ollama.com/install.sh | sh; fi
python - <<'PY'
import torch, transformers, peft, safetensors, httpx
print('gpu', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE')
print('torch', torch.__version__, 'transformers', transformers.__version__, 'peft', peft.__version__)
PY
free -g | head -2; df -h / /workspace 2>/dev/null; ollama --version
echo "env ok"
