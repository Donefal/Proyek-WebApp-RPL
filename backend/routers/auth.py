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
    Expected: {name, email, password, notelp}
    """
    try:
        # Validate password length (minimum 8 characters)
        if len(user_data.password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password harus minimal 8 karakter"
            )
        
        # Check if email already exists
        existing_customer = db.query(models.Customer).filter(
            models.Customer.email == user_data.email
        ).first()

        existing_admin = db.query(models.Admin).filter(
            models.Admin.email == user_data.email
        ).first()
        
        if existing_customer or existing_admin:
            raise HTTPException(
                status_code=409, 
                detail="Email sudah terdaftar"
            )
        
        # Hash password (simple hash for demo - use bcrypt in production)
        password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()
        
        # Create new customer
        new_customer = models.Customer(
            username=user_data.name,
            email=user_data.email,
            password=password_hash,
            notelp=user_data.notelp,
            saldo=0
        )
        
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
    Login user (customer or admin)
    Expected: {email, password}
    """
    try:
        # Hash the provided password
        password_hash = hashlib.sha256(credentials.password.encode()).hexdigest()
        
        # First, try to find as admin
        admin = db.query(models.Admin).filter(
            models.Admin.email == credentials.email
        ).first()
        
        if admin:
            # Verify admin password (support both hashed and plain text for backward compatibility)
            # In production, always use hashed passwords
            if admin.password:
                # Check if password matches (hashed or plain text)
                if admin.password == password_hash or admin.password == credentials.password:
                    token = create_access_token(admin.id_admin)
                    return {
                        "token": token,
                        "user": {
                            "id": str(admin.id_admin),
                            "name": admin.username,
                            "email": admin.email,
                            "role": "admin"
                        }
                    }
            raise HTTPException(
                status_code=401,
                detail="Email atau password salah"
            )
        
        # If not admin, try to find as customer
        customer = db.query(models.Customer).filter(
            models.Customer.email == credentials.email
        ).first()
        
        if not customer:
            raise HTTPException(
                status_code=401,
                detail="Email atau password salah"
            )
        
        # Verify customer password
        if customer.password and customer.password != password_hash:
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

