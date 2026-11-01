"""Execute Stage C with network connections blocked, including token counting."""
import os
from pathlib import Path
import runpy
import socket
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ['TIKTOKEN_CACHE_DIR'] = str(ROOT / '.cache/tiktoken')
sys.argv = ['label.py', '--dry-run', '--provider', 'openai', '--model', 'gpt-4o-mini'] + sys.argv[1:]
with patch.object(socket.socket, 'connect', side_effect=AssertionError('Offline verification: network forbidden')):
    runpy.run_module('training.data.label', run_name='__main__')
