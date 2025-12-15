from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
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

# GMT+7 timezone (WIB - Western Indonesian Time)
GMT7 = timezone(timedelta(hours=7))

def get_now_gmt7():
    """Get current datetime in GMT+7 timezone"""
    return datetime.now(GMT7)

def create_qr_token():
    """Generate QR token"""
    now = get_now_gmt7()
    return {
        "token": secrets.token_urlsafe(12),
        "expiresAt": (now + timedelta(minutes=QR_TTL_MINUTES)).isoformat()
    }

def calculate_parking_cost(start_time: datetime, end_time: Optional[datetime] = None):
    """Calculate parking cost"""
    if not end_time:
        end_time = get_now_gmt7()
    # Ensure both times are timezone-aware
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=GMT7)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=GMT7)
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
        # Availability is driven only by `booked` (business rule)
        is_available = not slot.booked

        # Derive human-readable status based on the requested combinations
        if not slot.booked and not slot.confirmed and not slot.occupied and not slot.alarmed:
            status = "available"
        elif slot.booked and not slot.confirmed and not slot.occupied and not slot.alarmed:
            status = "booked"
        elif slot.booked and slot.confirmed and not slot.occupied and not slot.alarmed:
            status = "confirmed"
        elif slot.booked and slot.confirmed and slot.occupied and not slot.alarmed:
            status = "occupied"
        elif (not slot.booked) and (not slot.confirmed) and slot.occupied and slot.alarmed:
            status = "alert"
        else:
            status = "unknown"

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
            "status": status,
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
    
    # Check if slot exists and availability based only on `booked`
    slot = db.query(models.Slot).filter(models.Slot.id_slot == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot tidak ditemukan")
    
    # Business rule: cannot book when already booked; occupied/alarmed do not block booking
    if slot.booked:
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
    
    # Generate QR token
    qr = create_qr_token()
    qr_expires_at = get_now_gmt7() + timedelta(minutes=QR_TTL_MINUTES)
    
    # Create booking
    new_booking = models.Booking(
        id_parkir=slot.id_slot,
        id_customer=user.id_customer,
        status="pending",
        qr_token=qr["token"],
        qr_expires_at=qr_expires_at
    )
    db.add(new_booking)
    
    # Mark slot as booked
    slot.booked = True
    db.commit()
    db.refresh(new_booking)
    
    return {
        "booking": {
            "id": f"B-{new_booking.id_booking}",
            "userId": str(user.id_customer),
            "spotId": spot_id_str,
            "qr": qr,
            "status": new_booking.status,
            "createdAt": new_booking.waktu_booking.isoformat() if new_booking.waktu_booking else get_now_gmt7().isoformat(),
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
    
    # Get slot info - id_parkir directly references slot.id_slot
    slot = db.query(models.Slot).filter(
        models.Slot.id_slot == booking.id_parkir
    ).first()
    
    if not slot:
        return {"booking": None}
    
    # Check if QR token expired for pending bookings
    if booking.status == "pending":
        now = get_now_gmt7()
        # Ensure qr_expires_at is timezone-aware for comparison
        if booking.qr_expires_at:
            if booking.qr_expires_at.tzinfo is None:
                # If stored without timezone, assume it's GMT+7
                qr_expires_at_aware = booking.qr_expires_at.replace(tzinfo=GMT7)
            else:
                qr_expires_at_aware = booking.qr_expires_at
            
            if qr_expires_at_aware < now:
                # Auto cancel expired booking
                booking.status = "cancelled"
                slot.booked = False
                db.commit()
                return {"booking": None}
        
        # Use existing QR token or generate new if missing
        if booking.qr_token and booking.qr_expires_at:
            qr = {
                "token": booking.qr_token,
                "expiresAt": booking.qr_expires_at.isoformat() if booking.qr_expires_at.tzinfo else booking.qr_expires_at.replace(tzinfo=GMT7).isoformat()
            }
        else:
            # Generate new QR token if missing
            qr = create_qr_token()
            booking.qr_token = qr["token"]
            booking.qr_expires_at = get_now_gmt7() + timedelta(minutes=QR_TTL_MINUTES)
            db.commit()
    else:
        # For checked-in, still return QR token if exists (for exit validation)
        if booking.qr_token and booking.qr_expires_at:
            qr = {
                "token": booking.qr_token,
                "expiresAt": booking.qr_expires_at.isoformat() if booking.qr_expires_at.tzinfo else booking.qr_expires_at.replace(tzinfo=GMT7).isoformat()
            }
        else:
            qr = None
    
    return {
        "booking": {
            "id": f"B-{booking.id_booking}",
            "userId": str(user.id_customer),
            "spotId": f"S{slot.id_slot}",
            "qr": qr,
            "status": booking.status,
            "createdAt": booking.waktu_booking.isoformat() if booking.waktu_booking else get_now_gmt7().isoformat(),
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
    
    # Get slot and mark as available - id_parkir directly references slot.id_slot
    slot = db.query(models.Slot).filter(
        models.Slot.id_slot == booking.id_parkir
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
    """Get parking history for current user - includes all statuses"""
    user = get_user_from_request(authorization, db)
    
    # Get all bookings except active ones (pending and checked-in are shown in active booking)
    # Include: cancelled, completed, and also pending/checked-in for history
    bookings = db.query(models.Booking).filter(
        models.Booking.id_customer == user.id_customer
    ).order_by(models.Booking.waktu_booking.desc()).all()
    
    history = []
    for booking in bookings:
        # Get slot info - id_parkir directly references slot.id_slot
        slot = db.query(models.Slot).filter(
            models.Slot.id_slot == booking.id_parkir
        ).first()
        
        # Calculate cost only for completed bookings
        cost = None
        duration_hours = None
        if booking.status == "completed" and booking.waktu_masuk and booking.waktu_keluar:
            cost_info = calculate_parking_cost(
                booking.waktu_masuk,
                booking.waktu_keluar
            )
            cost = cost_info["cost"]
            duration_hours = cost_info["hours"]
        elif booking.status == "checked-in" and booking.waktu_masuk:
            # For checked-in, calculate estimated cost
            cost_info = calculate_parking_cost(
                booking.waktu_masuk,
                get_now_gmt7()
            )
            cost = cost_info["cost"]
            duration_hours = cost_info["hours"]
        
        # Format status display
        status_display = {
            "pending": "Menunggu",
            "checked-in": "Sedang Parkir",
            "completed": "Selesai",
            "cancelled": "Dibatalkan"
        }.get(booking.status, booking.status)
        
        history.append({
            "bookingId": f"B-{booking.id_booking}",
            "userId": str(user.id_customer),
            "spotName": f"Slot {slot.id_slot}" if slot else "Unknown",
            "startTime": booking.waktu_masuk.isoformat() if booking.waktu_masuk else (booking.waktu_booking.isoformat() if booking.waktu_booking else None),
            "endTime": booking.waktu_keluar.isoformat() if booking.waktu_keluar else None,
            "durationHours": duration_hours,
            "cost": cost,
            "status": booking.status,
            "statusDisplay": status_display,
            "createdAt": booking.waktu_booking.isoformat() if booking.waktu_booking else None
        })
    
    return {"history": history}

