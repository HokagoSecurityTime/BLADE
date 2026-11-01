#!/usr/bin/env bash
# One-time setup on a fresh RunPod pod (PyTorch 2.x / CUDA 12.x template). Model downloads are cached on the volume.
set -euo pipefail
export HF_HOME=${HF_HOME:-/workspace/hf}
pip install -q unsloth
pip install -q lm-format-enforcer   # task B: JSON-schema constrained decoding (run_train.py --decoding stable); unused by default decoding
# unsloth upgrades torch but not the template's torchaudio; the stale torchaudio then breaks `import transformers` (libtorchaudio.so undefined symbol).
# Nothing here uses audio, so remove it when its torch pin no longer matches.
python - <<'PY' || pip uninstall -y -q torchaudio
import torch, torchaudio
PY
command -v tmux >/dev/null || (apt-get update -qq && apt-get install -y -qq tmux)
python - <<'PY'
import torch, transformers, trl, peft, unsloth, lmformatenforcer
print('gpu', torch.cuda.get_device_name(0), torch.cuda.get_device_properties(0).total_memory // 2**30, 'GB')
print('torch', torch.__version__, 'transformers', transformers.__version__, 'trl', trl.__version__, 'peft', peft.__version__, 'unsloth', unsloth.__version__, 'lm-format-enforcer', getattr(lmformatenforcer, '__version__', '?'))
PY
