from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    paid_credits = Column(Integer, default=0) 
    free_credits = Column(Integer, default=100) 
    predictions_count = Column(Integer, default=0)

    
    @property
    def total_credits(self):
        return self.paid_credits + self.free_credits

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float) 
    credits_added = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class PromoCode(Base):
    __tablename__ = "promocodes"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    reward = Column(Integer)
    max_uses = Column(Integer, default=10)
    current_uses = Column(Integer, default=0)
    is_active = Column(Boolean, default=True) 
    expiry_date = Column(DateTime, default=lambda: datetime.datetime.utcnow() + datetime.timedelta(days=30))

class UserPromo(Base):
    __tablename__ = "user_promos"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    promo_id = Column(Integer, ForeignKey("promocodes.id"))