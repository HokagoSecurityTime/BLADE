"""New controlled HTTP fixture, NOT an external project or production service.

No labels or review notes occur in the handler/guard source sent to the model.
Tokens are deterministic test identities, never real credentials.
"""
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

app = FastAPI(title="Observatory archive", version="1.0")
bearer = HTTPBearer(auto_error=False)
ACTORS = {
    "alice": {"sub": "alice", "tenant": "north", "role": "reader", "plan": "basic"},
    "bob": {"sub": "bob", "tenant": "north", "role": "reader", "plan": "basic"},
    "carol": {"sub": "carol", "tenant": "south", "role": "reader", "plan": "plus"},
    "dana": {"sub": "dana", "tenant": "south", "role": "admin", "plan": "basic"},
    "erin": {"sub": "erin", "tenant": "north", "role": "operator", "plan": "plus"},
    "alice_south": {"sub": "alice", "tenant": "south", "role": "reader", "plan": "basic"},
}


def actor(token: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if token is None or token.credentials not in ACTORS:
        raise HTTPException(401)
    return ACTORS[token.credentials]


def load(item_id: str):
    if item_id != "sample":
        raise HTTPException(404)
    return {"id": item_id, "owner": "alice", "tenant": "north", "value": "spectrum"}


def guard_a(user, item):
    if user["sub"] != item["owner"]:
        raise HTTPException(403)


def guard_b(user, item):
    if user["sub"] != item["owner"] and user["role"] != "admin":
        raise HTTPException(403)


def guard_c(user, item):
    if user["tenant"] != item["tenant"]:
        raise HTTPException(403)


def guard_d(user):
    if user["role"] != "operator":
        raise HTTPException(403)


def guard_e(user):
    if user["plan"] != "plus":
        raise HTTPException(403)


@app.get("/observations/{item_id}")
def observations(item_id: str, user=Depends(actor)):
    item = load(item_id)
    guard_a(user, item)
    return item


@app.get("/notebooks/{item_id}")
def notebooks(item_id: str, user=Depends(actor)):
    item = load(item_id)
    guard_a(user, item)
    return item


@app.get("/calibrations/{item_id}")
def calibrations(item_id: str, user=Depends(actor)):
    item = load(item_id)
    guard_b(user, item)
    return item


@app.get("/captures/{item_id}")
def captures(item_id: str, user=Depends(actor)):
    item = load(item_id)
    guard_b(user, item)
    return item


@app.get("/allocations/{item_id}")
def allocations(item_id: str, user=Depends(actor)):
    item = load(item_id)
    guard_c(user, item)
    return item


@app.get("/inventories/{item_id}")
def inventories(item_id: str, user=Depends(actor)):
    item = load(item_id)
    guard_c(user, item)
    return item


@app.get("/queues/{item_id}")
def queues(item_id: str, user=Depends(actor)):
    guard_d(user)
    return load(item_id)


@app.get("/relays/{item_id}")
def relays(item_id: str, user=Depends(actor)):
    guard_d(user)
    return load(item_id)


@app.get("/spectra/{item_id}")
def spectra(item_id: str, user=Depends(actor)):
    guard_e(user)
    return load(item_id)


@app.get("/forecasts/{item_id}")
def forecasts(item_id: str, user=Depends(actor)):
    guard_e(user)
    return load(item_id)


@app.get("/catalog/{item_id}")
def catalog(item_id: str):
    """Public reference catalog; no authentication is required."""
    return load(item_id)


@app.get("/bulletins/{item_id}")
def bulletins(item_id: str):
    """Public reference bulletins; no authentication is required."""
    return load(item_id)


@app.get("/transfers/{item_id}")
def transfers(item_id: str, user=Depends(actor)):
    item = load(item_id)
    guard_a(user, item)
    guard_c(user, item)
    return item


@app.get("/reservations/{item_id}")
def reservations(item_id: str, user=Depends(actor)):
    item = load(item_id)
    guard_c(user, item)
    guard_e(user)
    return item
