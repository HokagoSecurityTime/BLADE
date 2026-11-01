"""Sequential local baseline queue; no concurrent requests to Ollama."""
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[2]
metrics_path = root/'reports/eval/b_qwen2.5_7b_v2.0_2026-10-20_metrics.json'
while True:
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding='utf-8'))
        if metrics['state'] in {'complete', 'blocked_provider_errors'}:
            break
    time.sleep(15)
subprocess.run([sys.executable, '-m', 'scripts.eval_classifier', '--configuration', 'c',
                '--test-sha256', 'bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa'], cwd=root, check=True)
