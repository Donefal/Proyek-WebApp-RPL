from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional

import backend.models as models
from backend.database import get_db

router = APIRouter()

FIRST_HOUR_RATE = 10000
EXTRA_HOUR_RATE = 5000

# GMT+7 timezone (WIB - Western Indonesian Time)
GMT7 = timezone(timedelta(hours=7))

def get_now_gmt7():
    """Get current datetime in GMT+7 timezone"""
    return datetime.now(GMT7)

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
        # Availability is driven only by `booked`
        is_available = not slot.booked

        # Derive status consistent with user view
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
    booking = db.query(models.Booking).filter(
        models.Booking.qr_token == qr_token,
        models.Booking.status.in_(["pending", "checked-in"])
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="QR tidak ditemukan atau sudah tidak valid")
    
    # Check if QR token expired
    # Note: Expiry only blocks "enter". For "exit" (checked-in), allow even if QR past TTL.
    now = get_now_gmt7()
    if action == "enter":
        if booking.qr_expires_at:
            if booking.qr_expires_at.tzinfo is None:
                qr_expires_at_aware = booking.qr_expires_at.replace(tzinfo=GMT7)
            else:
                qr_expires_at_aware = booking.qr_expires_at
            if qr_expires_at_aware < now:
                raise HTTPException(status_code=400, detail="QR code sudah kadaluarsa")
    
    if action == "enter":
        if booking.status == "checked-in":
            raise HTTPException(status_code=400, detail="Kedatangan sudah dikonfirmasi")
        
        # Mark as checked-in
        booking.status = "checked-in"
        booking.waktu_masuk = get_now_gmt7()
        
        # Mark slot as confirmed - id_parkir directly references slot.id_slot
        slot = db.query(models.Slot).filter(
            models.Slot.id_slot == booking.id_parkir
        ).first()
        if slot:
            slot.confirmed = True
        
        # Update aktuator kondisi_buka untuk gate masuk (idGate: 1)
        aktuator = db.query(models.Aktuator).filter(models.Aktuator.id_aktuator == 1).first()
        if aktuator:
            aktuator.kondisi_buka = True
        
        db.commit()
        return {
            "message": "Masuk Dikonfirmasi Admin",
            "idGate": 1,
            "kondisi_buka": True
        }
    
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
        booking.waktu_keluar = get_now_gmt7()
        
        # Free up slot - id_parkir directly references slot.id_slot
        slot = db.query(models.Slot).filter(
            models.Slot.id_slot == booking.id_parkir
        ).first()
        if slot:
            slot.booked = False
            slot.occupied = False
            slot.confirmed = False
        
        # Update aktuator kondisi_buka untuk gate keluar (idGate: 2)
        aktuator = db.query(models.Aktuator).filter(models.Aktuator.id_aktuator == 2).first()
        if aktuator:
            aktuator.kondisi_buka = True
        
        db.commit()
        return {
            "message": "Keluar Dikonfirmasi Admin",
            "idGate": 2,
            "kondisi_buka": True
        }
    
    else:
        raise HTTPException(status_code=400, detail="Aksi tidak dikenal")

@router.get("/admin/reports")
def get_reports(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    """Get admin reports"""
    try:
        get_admin_from_request(authorization, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authorization failed: {str(e)}")
    
    try:
        # Calculate today's date range - convert to timezone-naive for MySQL compatibility
        now = get_now_gmt7()
        # MySQL stores datetime as timezone-naive, so convert comparison times to naive
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Convert to naive datetime for MySQL comparison (strip timezone info)
        if today_start.tzinfo:
            today_start_naive = today_start.replace(tzinfo=None)
        else:
            today_start_naive = today_start
        
        if today_end.tzinfo:
            today_end_naive = today_end.replace(tzinfo=None)
        else:
            today_end_naive = today_end
        
        # Get today's completed bookings - only where waktu_keluar is not None
        today_bookings = db.query(models.Booking).filter(
            models.Booking.status == "completed",
            models.Booking.waktu_keluar.isnot(None),
            models.Booking.waktu_keluar >= today_start_naive,
            models.Booking.waktu_keluar < today_end_naive
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
            
            # Compare with naive datetime
            if booking.waktu_masuk:
                waktu_masuk_naive = booking.waktu_masuk.replace(tzinfo=None) if booking.waktu_masuk.tzinfo else booking.waktu_masuk
                if waktu_masuk_naive >= today_start_naive:
                    today_entries += 1
            
            if booking.waktu_keluar:
                waktu_keluar_naive = booking.waktu_keluar.replace(tzinfo=None) if booking.waktu_keluar.tzinfo else booking.waktu_keluar
                if waktu_keluar_naive >= today_start_naive:
                    today_exits += 1
        
        # Calculate month revenue
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month_start.tzinfo:
            month_start_naive = month_start.replace(tzinfo=None)
        else:
            month_start_naive = month_start
        
        month_bookings = db.query(models.Booking).filter(
            models.Booking.status == "completed",
            models.Booking.waktu_keluar.isnot(None),
            models.Booking.waktu_keluar >= month_start_naive
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
    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"Error in get_reports: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

