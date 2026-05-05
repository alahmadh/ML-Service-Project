from app.database import SessionLocal, engine
from app.models import Base, PromoCode
from datetime import datetime, timedelta

def init():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        if not db.query(PromoCode).filter(PromoCode.code == "WINE2026").first():
            promo = PromoCode(
                code="WINE2026", 
                reward=100,      
                max_uses=50,     
                current_uses=0,
                expiry_date=datetime.utcnow() + timedelta(days=30) 
            )
            db.add(promo)
            db.commit()
            print("✅ Promo code 'WINE2026' created successfully!")
        else:
            print("ℹ️ Promo code already exists.")
    except Exception as e:
        print(f"❌ Error initializing DB: {e}")
    finally:
        db.close()
    
    print("PostgreSQL Initialized!")

if __name__ == "__main__":
    init()