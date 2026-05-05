from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import jwt
from passlib.context import CryptContext
from prometheus_fastapi_instrumentator import Instrumentator
from . import models, database, tasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import datetime

app = FastAPI()
Instrumentator().instrument(app).expose(app)

SECRET_KEY = "WINE_SECRET_2026"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

models.Base.metadata.create_all(bind=database.engine)

class RegisterSchema(BaseModel):
    username: str
    password: str

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = db.query(models.User).filter(models.User.username == username).first()
        if user is None: raise HTTPException(status_code=401)
        return user
    except: raise HTTPException(status_code=401)

@app.post("/register")
def register(user_data: RegisterSchema, db: Session = Depends(database.get_db)):
    hashed = pwd_context.hash(user_data.password)
    new_user = models.User(username=user_data.username, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    return {"message": "Success"}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401)
    token = jwt.encode({"sub": user.username}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/me")
def me(user: models.User = Depends(get_current_user)):
    return {
        "username": user.username, 
        "total_credits": user.free_credits + user.paid_credits,
        "free_credits": user.free_credits,
        "paid_credits": user.paid_credits,
        "predictions_count": user.predictions_count
    }

@app.post("/predict")
def predict(data: dict, user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    cost = 10 if user.predictions_count < 5 else 5
    
    if (user.free_credits + user.paid_credits) < cost:
        raise HTTPException(status_code=400, detail="No credits")

    task = tasks.run_prediction_task.delay(data)
    result = task.get(timeout=10)

    if user.free_credits >= cost:
        user.free_credits -= cost
    else:
        remaining_cost = cost - user.free_credits
        user.free_credits = 0
        user.paid_credits -= remaining_cost

    user.predictions_count += 1
    db.commit() 
    return {"quality": result, "remaining_total": (user.free_credits + user.paid_credits)}

@app.post("/billing/recharge")
def recharge(amount: float, user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    credits_to_add = int(amount * 10)
    new_trans = models.Transaction(user_id=user.id, amount=amount, credits_added=credits_to_add)
    
    user.paid_credits += credits_to_add
    db.add(new_trans)
    db.commit()
    return {"message": "Success", "paid_balance": user.paid_credits}

@app.post("/promo")
def apply_promo(promo_code: str, user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    promo = db.query(models.PromoCode).filter(models.PromoCode.code == promo_code).first()
    if not promo or not promo.is_active:
        raise HTTPException(status_code=404, detail="Promo code not found")
    if datetime.datetime.utcnow() > promo.expiry_date:
        promo.is_active = False
        db.commit()
        raise HTTPException(status_code=400, detail="Promo code expired")
    if promo.current_uses >= promo.max_uses:
        raise HTTPException(status_code=400, detail="Maximum usage limit reached")
    
    already_used = db.query(models.UserPromo).filter(models.UserPromo.user_id == user.id, models.UserPromo.promo_id == promo.id).first()
    if already_used:
        raise HTTPException(status_code=400, detail="You have already redeemed this promo code")

    user.free_credits += promo.reward
    promo.current_uses += 1
    db.add(models.UserPromo(user_id=user.id, promo_id=promo.id))
    db.commit()
    return {"message": "Promo applied successfully", "free_balance": user.free_credits}