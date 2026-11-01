"""Static-analysis fixture; never imported as a live backend."""
from fastapi import FastAPI, Depends, HTTPException

app = FastAPI()


@app.get('/users/{userId}')
def get_user(userId: str, current_user=Depends(get_current_user)):
    if 'admin' in current_user.roles:
        return db.get_user(userId)
    if current_user.id != userId:
        raise HTTPException(status_code=403)
    return db.get_user(userId)


@app.get('/orgs/{orgId}/docs')
def documents(orgId: str, current_user=Depends(get_current_user)):
    if current_user.tenant_id == orgId:
        return db.docs(orgId)
    raise HTTPException(403)


@app.get('/orders/{orderId}')
def order(orderId: str, current_user=Depends(get_current_user)):
    return db.query(Order).filter(Order.user_id == current_user.id).first()
