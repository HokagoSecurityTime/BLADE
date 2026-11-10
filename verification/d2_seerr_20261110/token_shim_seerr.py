"""BLADE-token -> Seerr API-key translation layer (sits between the BLADE proxy and Seerr).

Copied from verification/mealie_runtime/token_shim.py (Mealie precedent) with the header swap changed for Seerr:
Seerr's auth middleware (server/middleware/auth.ts, v3.5.1) accepts `X-API-Key: <settings.main.apiKey>` and then acts
as the user named by `X-API-User: <user id>` (default user 1). So this shim verifies the BLADE JWT with
BLADE_JWT_SECRET, takes `sub` (Seerr integer user id) and forwards the request with those two headers instead of
Authorization. It makes no authorization decision of its own; anonymous or unverifiable requests are forwarded
unchanged (no API key attached). Seerr application code is not modified.

Env: BLADE_JWT_SECRET, SEERR_API_KEY (settings.main.apiKey), SEERR_URL (http://127.0.0.1:5055), SHIM_HOST/SHIM_PORT.
"""
import logging
import os

import jwt
from aiohttp import ClientSession, web

BLADE_SECRET = os.environ["BLADE_JWT_SECRET"]
SEERR_API_KEY = os.environ["SEERR_API_KEY"]
SEERR = os.getenv("SEERR_URL", "http://127.0.0.1:5055").rstrip("/")
HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers",
       "transfer-encoding", "upgrade", "host", "content-length", "accept-encoding", "content-encoding"}


def translate(auth: str | None) -> str | None:
    parts = auth.split() if auth else []
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    try:
        claims = jwt.decode(parts[1], BLADE_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None
    sub = claims.get("sub")
    try:
        return str(int(sub))
    except (ValueError, TypeError):
        return None


async def handle(request: web.Request) -> web.StreamResponse:
    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP}
    user_id = translate(request.headers.get("Authorization"))
    headers.pop("Authorization", None)
    headers.pop("Cookie", None)
    if user_id:
        headers["X-API-Key"] = SEERR_API_KEY
        headers["X-API-User"] = user_id
    headers["X-Blade-Shim"] = "swapped" if user_id else "passthrough"
    body = await request.read()
    session: ClientSession = request.app["session"]
    async with session.request(request.method, SEERR + request.raw_path, headers=headers, data=body,
                               allow_redirects=False) as resp:
        out = {k: v for k, v in resp.headers.items() if k.lower() not in HOP}
        out["X-Blade-Shim"] = headers["X-Blade-Shim"]
        return web.Response(status=resp.status, headers=out, body=await resp.read())


async def make_app() -> web.Application:
    app = web.Application(client_max_size=50 * 1024 * 1024)
    app["session"] = ClientSession()

    async def close(_app):
        await app["session"].close()
    app.on_cleanup.append(close)
    app.router.add_route("*", "/{path:.*}", handle)
    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    web.run_app(make_app(), host=os.getenv("SHIM_HOST", "127.0.0.1"), port=int(os.getenv("SHIM_PORT", "5056")))
