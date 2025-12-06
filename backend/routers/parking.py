from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import secrets

import backend.models as models
import backend.schemas as schemas
from backend.database import get_db

router = APIRouter()

# QR Token TTL (30 minutes)
QR_TTL_MINUTES = 30
FIRST_HOUR_RATE = 10000
EXTRA_HOUR_RATE = 5000

def create_qr_token():
    """Generate QR token"""
    return {
        "token": secrets.token_urlsafe(12),
        "expiresAt": (datetime.utcnow() + timedelta(minutes=QR_TTL_MINUTES)).isoformat()
    }

def calculate_parking_cost(start_time: datetime, end_time: Optional[datetime] = None):
    """Calculate parking cost"""
    if not end_time:
        end_time = datetime.utcnow()
    elapsed_ms = (end_time - start_time).total_seconds() * 1000
    hours = max(1, int((elapsed_ms / (60 * 60 * 1000)) + 0.99))  # Round up
    cost = FIRST_HOUR_RATE + max(0, hours - 1) * EXTRA_HOUR_RATE
    return {"hours": hours, "cost": cost}

def get_current_user_id(token: Optional[str] = None) -> Optional[int]:
    """Extract user ID from token (simplified - in production use proper JWT)"""
    # For now, we'll use a simple approach
    # In production, decode JWT token properly
    if not token:
        return None
    # Simple token format: "token-{user_id}"
    try:
        if token.startswith("token-"):
            return int(token.split("token-")[1])
        # Try to extract from Authorization header format
        if "Bearer" in token:
            token = token.replace("Bearer", "").strip()
        # For demo, accept any numeric ID
        return int(token) if token.isdigit() else None
    except:
        return None

def get_user_from_request(authorization: Optional[str] = None, db: Session = Depends(get_db)):
    """Get user from authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_id = get_current_user_id(authorization.replace("Bearer ", "").strip() if authorization else None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = db.query(models.Customer).filter(models.Customer.id_customer == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@router.get("/parking/spots")
def get_spots(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    """Get all parking spots with availability status"""
    # Get all slots
    slots = db.query(models.Slot).all()
    
    spots = []
    for slot in slots:
        # Check if slot is booked
        is_booked = slot.booked
        is_occupied = slot.occupied
        is_available = not is_booked and not is_occupied
        
        # Get mikrokontroler info
        mikrokontroler = db.query(models.Mikrokontroler).filter(
            models.Mikrokontroler.id_mikrokontroler == slot.id_mikrokontroler
        ).first()
        
        spots.append({
            "id": f"S{slot.id_slot}",
            "name": f"Slot {slot.id_slot}",
            "code": f"P-{slot.id_slot}",
            "level": 1,
            "isAvailable": is_available,
            "ratePerHour": FIRST_HOUR_RATE
        })
    
    return {"spots": spots}

@router.post("/parking/book")
def create_booking(
    booking_data: dict,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    """Create a new booking"""
    user = get_user_from_request(authorization, db)
    
    spot_id_str = booking_data.get("spotId")
    if not spot_id_str:
        raise HTTPException(status_code=400, detail="spotId diperlukan")
    
    # Extract slot number from spotId (format: "S1", "S2", etc.)
    try:
        slot_id = int(spot_id_str.replace("S", ""))
    except:
        raise HTTPException(status_code=400, detail="spotId tidak valid")
    
    # Check if slot exists and is available
    slot = db.query(models.Slot).filter(models.Slot.id_slot == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot tidak ditemukan")
    
    if slot.booked or slot.occupied:
        raise HTTPException(status_code=400, detail="Lahan tidak tersedia")
    
    # Check for existing active booking
    existing_booking = db.query(models.Booking).filter(
        models.Booking.id_customer == user.id_customer,
        models.Booking.status.in_(["pending", "checked-in"])
    ).first()
    
    if existing_booking:
        # Check if expired
        if existing_booking.status == "pending":
            # For simplicity, allow only one active booking
            raise HTTPException(status_code=400, detail="Masih ada booking aktif")
    
    # Get mikrokontroler for this slot
    mikrokontroler = db.query(models.Mikrokontroler).filter(
        models.Mikrokontroler.id_mikrokontroler == slot.id_mikrokontroler
    ).first()
    
    if not mikrokontroler:
        raise HTTPException(status_code=404, detail="Mikrokontroler tidak ditemukan")
    
    # Create booking
    new_booking = models.Booking(
        id_parkir=mikrokontroler.id_mikrokontroler,
        id_customer=user.id_customer,
        status="pending"
    )
    db.add(new_booking)
    
    # Mark slot as booked
    slot.booked = True
    db.commit()
    db.refresh(new_booking)
    
    # Generate QR token
    qr = create_qr_token()
    
    return {
        "booking": {
            "id": f"B-{new_booking.id_booking}",
            "userId": str(user.id_customer),
            "spotId": spot_id_str,
            "qr": qr,
            "status": new_booking.status,
            "createdAt": new_booking.waktu_booking.isoformat() if new_booking.waktu_booking else datetime.utcnow().isoformat(),
            "startTime": None,
            "endTime": None,
            "cost": None
        }
    }

@router.get("/parking/active")
def get_active_booking(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    """Get active booking for current user"""
    user = get_user_from_request(authorization, db)
    
    booking = db.query(models.Booking).filter(
        models.Booking.id_customer == user.id_customer,
        models.Booking.status.in_(["pending", "checked-in"])
    ).first()
    
    if not booking:
        return {"booking": None}
    
    # Get slot info
    slot = db.query(models.Slot).join(models.Mikrokontroler).filter(
        models.Mikrokontroler.id_mikrokontroler == booking.id_parkir
    ).first()
    
    if not slot:
        return {"booking": None}
    
    # Generate QR token (for pending bookings)
    qr = None
    if booking.status == "pending":
        qr = create_qr_token()
    else:
        # For checked-in, use existing token or generate new
        qr = create_qr_token()
    
    return {
        "booking": {
            "id": f"B-{booking.id_booking}",
            "userId": str(user.id_customer),
            "spotId": f"S{slot.id_slot}",
            "qr": qr,
            "status": booking.status,
            "createdAt": booking.waktu_booking.isoformat() if booking.waktu_booking else datetime.utcnow().isoformat(),
            "startTime": booking.waktu_masuk.isoformat() if booking.waktu_masuk else None,
            "endTime": booking.waktu_keluar.isoformat() if booking.waktu_keluar else None,
            "cost": None
        }
    }

@router.post("/parking/cancel")
def cancel_booking(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    """Cancel active booking"""
    user = get_user_from_request(authorization, db)
    
    booking = db.query(models.Booking).filter(
        models.Booking.id_customer == user.id_customer,
        models.Booking.status == "pending"
    ).first()
    
    if not booking:
        raise HTTPException(status_code=400, detail="Tidak ada booking yang bisa dibatalkan")
    
    # Get slot and mark as available
    slot = db.query(models.Slot).join(models.Mikrokontroler).filter(
        models.Mikrokontroler.id_mikrokontroler == booking.id_parkir
    ).first()
    
    if slot:
        slot.booked = False
    
    booking.status = "cancelled"
    db.commit()
    
    return {"message": "Booking berhasil dibatalkan"}

@router.get("/parking/history")
def get_history(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    """Get parking history for current user"""
    user = get_user_from_request(authorization, db)
    
    bookings = db.query(models.Booking).filter(
        models.Booking.id_customer == user.id_customer,
        models.Booking.status == "completed"
    ).order_by(models.Booking.waktu_keluar.desc()).all()
    
    history = []
    for booking in bookings:
        # Get slot info
        slot = db.query(models.Slot).join(models.Mikrokontroler).filter(
            models.Mikrokontroler.id_mikrokontroler == booking.id_parkir
        ).first()
        
        # Calculate cost
        cost_info = calculate_parking_cost(
            booking.waktu_masuk if booking.waktu_masuk else booking.waktu_booking,
            booking.waktu_keluar
        )
        
        history.append({
            "bookingId": f"B-{booking.id_booking}",
            "userId": str(user.id_customer),
            "spotName": f"Slot {slot.id_slot}" if slot else "Unknown",
            "startTime": booking.waktu_masuk.isoformat() if booking.waktu_masuk else None,
            "endTime": booking.waktu_keluar.isoformat() if booking.waktu_keluar else None,
            "durationHours": cost_info["hours"],
            "cost": cost_info["cost"]
        })
    
    return {"history": history}

