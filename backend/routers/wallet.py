from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

import backend.models as models
from backend.database import get_db

router = APIRouter()

def get_user_from_request(authorization: Optional[str] = None, db: Session = Depends(get_db)):
    """Get user from authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Simple token extraction (in production, use proper JWT)
    token = authorization.replace("Bearer ", "").strip()
    try:
        if token.startswith("token-"):
            user_id = int(token.split("token-")[1])
        else:
            user_id = int(token) if token.isdigit() else None
    except:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = db.query(models.Customer).filter(models.Customer.id_customer == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@router.get("/wallet")
def get_wallet_balance(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    """Get wallet balance for current user"""
    user = get_user_from_request(authorization, db)
    
    # Get customer with latest balance
    customer = db.query(models.Customer).filter(
        models.Customer.id_customer == user.id_customer
    ).first()
    
    balance = customer.saldo if customer else 0
    
    return {"balance": balance}

@router.post("/wallet/topup")
def topup_wallet(
    topup_data: dict,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    """Top up wallet balance"""
    user = get_user_from_request(authorization, db)
    
    amount = topup_data.get("amount")
    if not amount or amount <= 0:
        raise HTTPException(status_code=400, detail="Nominal tidak valid")
    
    # Get customer
    customer = db.query(models.Customer).filter(
        models.Customer.id_customer == user.id_customer
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    
    # Update balance
    customer.saldo = (customer.saldo or 0) + int(amount)
    db.commit()
    db.refresh(customer)
    
    return {"balance": customer.saldo}

