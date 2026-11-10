#!/bin/bash
# BLADE proxy for the Seerr run: 127.0.0.3:8080 -> token shim 5056 -> Seerr 5055. Runtime code unmodified.
ROOT=/c/BLADE/verification/d2_seerr_20261110
cd "$ROOT/blade" && source "$ROOT/blade/env.sh"
exec python -m proxy.server
