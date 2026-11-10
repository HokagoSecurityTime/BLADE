#!/bin/bash
# Token shim 5056: BLADE JWT (Authorization) -> Seerr X-API-Key + X-API-User. No authorization decision of its own.
ROOT=/c/BLADE/verification/d2_seerr_20261110
cd "$ROOT" && source "$ROOT/blade/env.sh"
exec python token_shim_seerr.py
