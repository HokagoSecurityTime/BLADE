"""S4-3 step 1: environment gate (H100 SXM plan; A100 / Blackwell also accepted with a warning). Exit 0 = pass, 1 = stop and report.
Checks: torch >= 2.4 with CUDA >= 12.1, device capability (9, 0) = H100 (warn if different GPU), transformers / peft / bitsandbytes importable,
bitsandbytes 4-bit kernels work on this GPU (tiny Linear4bit forward), sdpa attention available. Writes out/env_check.json."""
from __future__ import annotations
import json, sys, traceback
from pathlib import Path

out = Path(sys.argv[1] if len(sys.argv) > 1 else 'out/env_check.json'); out.parent.mkdir(parents=True, exist_ok=True); res = dict(checks={}, ok=True)
def chk(name, ok, info=''):
    res['checks'][name] = dict(ok=bool(ok), info=str(info)); res['ok'] = res['ok'] and bool(ok); print(f"[{'ok' if ok else 'FAIL'}] {name}: {info}")
try:
    import torch
    v = tuple(int(x) for x in torch.__version__.split('+')[0].split('.')[:2]); cu = torch.version.cuda or '0'
    chk('torch>=2.4', v >= (2, 4), torch.__version__); chk('cuda>=12.1', tuple(int(x) for x in cu.split('.')[:2]) >= (12, 1), cu)
    cap = torch.cuda.get_device_capability(0); chk('gpu', True, f'{torch.cuda.get_device_name(0)} capability {cap} vram {torch.cuda.get_device_properties(0).total_memory // 2**30} GB')
    if cap != (9, 0): print(f'[warn] capability {cap} != (9, 0): not the H100 this run was planned for (A100=(8,0), Blackwell=(12,0) also run)')
    import transformers, peft; chk('transformers', True, transformers.__version__); chk('peft', True, peft.__version__)
    try:
        import bitsandbytes as bnb; chk('bitsandbytes import', True, bnb.__version__)
        from bitsandbytes.nn import Linear4bit
        lin = Linear4bit(64, 64, bias=False, compute_dtype=torch.bfloat16, quant_type='nf4').cuda(); y = lin(torch.randn(2, 64, device='cuda', dtype=torch.bfloat16))
        chk('bitsandbytes 4bit forward on this GPU', torch.isfinite(y).all().item(), f'output {tuple(y.shape)}')
    except Exception as e: chk('bitsandbytes 4bit forward on this GPU', False, f'{type(e).__name__}: {e}'); traceback.print_exc()
    try:
        q = torch.randn(1, 1, 4, 8, device='cuda', dtype=torch.bfloat16); torch.nn.functional.scaled_dot_product_attention(q, q, q); chk('sdpa', True, 'scaled_dot_product_attention ok')
    except Exception as e: chk('sdpa', False, str(e))
    try:
        import flash_attn; print(f'[info] flash_attn {flash_attn.__version__} is installed but will NOT be used (attn_implementation=sdpa)')
    except Exception: print('[info] flash_attn not installed (fine)')
except Exception as e:
    chk('environment', False, f'{type(e).__name__}: {e}'); traceback.print_exc()
out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8'); print('ENV_OK=' + ('1' if res['ok'] else '0')); sys.exit(0 if res['ok'] else 1)
