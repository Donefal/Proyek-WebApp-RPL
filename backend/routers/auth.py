from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib

import backend.models as models
import backend.schemas as schemas
from backend.database import get_db

router = APIRouter()

# Simple token generation (for demo - in production use proper JWT)
def create_access_token(user_id: int) -> str:
    """Create simple access token"""
    return f"token-{user_id}"

@router.post("/auth/register")
def register(user_data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    """
    Register new customer
    Expected: {name, email, password}
    """
    try:
        # Check if email already exists
        existing_customer = db.query(models.Customer).filter(
            models.Customer.email == user_data.email
        ).first()
        
        if existing_customer:
            raise HTTPException(
                status_code=409, 
                detail="Email sudah terdaftar"
            )
        
        # Create new customer
        new_customer = models.Customer(
            username=user_data.name,
            email=user_data.email,
            notelp="",  # Default, bisa diupdate nanti
            saldo=0
        )
        # Note: Untuk production, password harus di-hash dan disimpan di tabel terpisah
        # Untuk sekarang, kita skip password karena model Customer tidak punya field password
        
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)
        
        return {"message": "Registrasi berhasil"}
    
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email sudah terdaftar atau data tidak valid"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan: {str(e)}"
        )

@router.post("/auth/login")
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Login user
    Expected: {email, password}
    """
    try:
        # Find customer by email
        customer = db.query(models.Customer).filter(
            models.Customer.email == credentials.email
        ).first()
        
        # For demo: accept any password if customer exists
        # In production, verify password hash
        if not customer:
            raise HTTPException(
                status_code=401,
                detail="Email atau password salah"
            )
        
        # Create token
        token = create_access_token(customer.id_customer)
        
        return {
            "token": token,
            "user": {
                "id": str(customer.id_customer),
                "name": customer.username,
                "email": customer.email,
                "role": "user"
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan: {str(e)}"
        )

