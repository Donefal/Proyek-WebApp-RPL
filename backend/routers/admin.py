from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

import backend.models as models
from backend.database import get_db

router = APIRouter()

FIRST_HOUR_RATE = 10000
EXTRA_HOUR_RATE = 5000

def get_admin_from_request(authorization: Optional[str] = None, db: Session = Depends(get_db)):
    """Get admin from authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Simple token extraction (in production, use proper JWT)
    token = authorization.replace("Bearer ", "").strip()
    try:
        if token.startswith("token-"):
            admin_id = int(token.split("token-")[1])
        else:
            admin_id = int(token) if token.isdigit() else None
    except:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if not admin_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Check if user is admin (for demo, accept any user)
    # In production, check role properly
    admin = db.query(models.Admin).filter(models.Admin.id_admin == admin_id).first()
    if not admin:
        # For demo, also accept customer as admin
        customer = db.query(models.Customer).filter(models.Customer.id_customer == admin_id).first()
        if not customer:
            raise HTTPException(status_code=401, detail="User not found")
    
    return admin_id

def calculate_parking_cost(start_time: datetime, end_time: Optional[datetime] = None):
    """Calculate parking cost"""
    if not end_time:
        end_time = datetime.utcnow()
    elapsed_ms = (end_time - start_time).total_seconds() * 1000
    hours = max(1, int((elapsed_ms / (60 * 60 * 1000)) + 0.99))  # Round up
    cost = FIRST_HOUR_RATE + max(0, hours - 1) * EXTRA_HOUR_RATE
    return {"hours": hours, "cost": cost}

@router.get("/admin/spots")
def get_admin_spots(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    """Get all parking spots for admin view"""
    get_admin_from_request(authorization, db)
    
    slots = db.query(models.Slot).all()
    
    spots = []
    for slot in slots:
        is_booked = slot.booked
        is_occupied = slot.occupied
        is_available = not is_booked and not is_occupied
        
        spots.append({
            "id": f"S{slot.id_slot}",
            "name": f"Slot {slot.id_slot}",
            "code": f"P-{slot.id_slot}",
            "level": 1,
            "isAvailable": is_available,
            "ratePerHour": FIRST_HOUR_RATE
        })
    
    return {"spots": spots}

@router.post("/admin/scan")
def scan_qr(
    scan_data: dict,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    """Scan QR code for entry/exit validation"""
    get_admin_from_request(authorization, db)
    
    qr_token = scan_data.get("qrToken")
    action = scan_data.get("action")
    
    if not qr_token or not action:
        raise HTTPException(status_code=400, detail="qrToken dan action diperlukan")
    
    # Find booking by QR token
    # For now, we'll search by booking ID in the token
    # In production, store QR token in booking table
    try:
        # Extract booking ID from token (format: "B-123" or similar)
        # For demo, we'll search all pending/checked-in bookings
        bookings = db.query(models.Booking).filter(
            models.Booking.status.in_(["pending", "checked-in"])
        ).all()
        
        booking = None
        for b in bookings:
            # Simple matching - in production, store QR token in database
            booking_id_str = f"B-{b.id_booking}"
            if qr_token in booking_id_str or booking_id_str in qr_token:
                booking = b
                break
        
        if not booking:
            raise HTTPException(status_code=404, detail="QR tidak ditemukan")
    except Exception as e:
        raise HTTPException(status_code=404, detail="QR tidak ditemukan")
    
    if action == "enter":
        if booking.status == "checked-in":
            raise HTTPException(status_code=400, detail="Kedatangan sudah dikonfirmasi")
        
        # Mark as checked-in
        booking.status = "checked-in"
        booking.waktu_masuk = datetime.utcnow()
        
        # Mark slot as confirmed
        slot = db.query(models.Slot).join(models.Mikrokontroler).filter(
            models.Mikrokontroler.id_mikrokontroler == booking.id_parkir
        ).first()
        if slot:
            slot.confirmed = True
        
        db.commit()
        return {"message": "Masuk dikonfirmasi admin"}
    
    elif action == "exit":
        if booking.status != "checked-in":
            raise HTTPException(status_code=400, detail="Belum masuk atau sudah selesai")
        
        # Get customer
        customer = db.query(models.Customer).filter(
            models.Customer.id_customer == booking.id_customer
        ).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
        
        # Calculate cost
        start_time = booking.waktu_masuk if booking.waktu_masuk else booking.waktu_booking
        cost_info = calculate_parking_cost(start_time)
        
        # Check wallet balance
        if (customer.saldo or 0) < cost_info["cost"]:
            raise HTTPException(status_code=400, detail="Saldo user tidak cukup")
        
        # Deduct from wallet
        customer.saldo = (customer.saldo or 0) - cost_info["cost"]
        
        # Update booking
        booking.status = "completed"
        booking.waktu_keluar = datetime.utcnow()
        
        # Free up slot
        slot = db.query(models.Slot).join(models.Mikrokontroler).filter(
            models.Mikrokontroler.id_mikrokontroler == booking.id_parkir
        ).first()
        if slot:
            slot.booked = False
            slot.occupied = False
            slot.confirmed = False
        
        db.commit()
        return {"message": "Keluar dikonfirmasi admin"}
    
    else:
        raise HTTPException(status_code=400, detail="Aksi tidak dikenal")

@router.get("/admin/reports")
def get_reports(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    """Get admin reports"""
    get_admin_from_request(authorization, db)
    
    # Calculate today's date range
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # Get today's completed bookings
    today_bookings = db.query(models.Booking).filter(
        models.Booking.status == "completed",
        models.Booking.waktu_keluar >= today_start,
        models.Booking.waktu_keluar < today_end
    ).all()
    
    # Calculate revenue
    today_revenue = 0
    today_entries = 0
    today_exits = 0
    
    for booking in today_bookings:
        if booking.waktu_masuk and booking.waktu_keluar:
            start_time = booking.waktu_masuk
            end_time = booking.waktu_keluar
            cost_info = calculate_parking_cost(start_time, end_time)
            today_revenue += cost_info["cost"]
        
        if booking.waktu_masuk and booking.waktu_masuk >= today_start:
            today_entries += 1
        
        if booking.waktu_keluar and booking.waktu_keluar >= today_start:
            today_exits += 1
    
    # Calculate month revenue
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_bookings = db.query(models.Booking).filter(
        models.Booking.status == "completed",
        models.Booking.waktu_keluar >= month_start
    ).all()
    
    month_revenue = 0
    for booking in month_bookings:
        if booking.waktu_masuk and booking.waktu_keluar:
            start_time = booking.waktu_masuk
            end_time = booking.waktu_keluar
            cost_info = calculate_parking_cost(start_time, end_time)
            month_revenue += cost_info["cost"]
    
    return {
        "reports": {
            "todayRevenue": today_revenue,
            "monthRevenue": month_revenue,
            "todayEntries": today_entries,
            "todayExits": today_exits
        }
    }

