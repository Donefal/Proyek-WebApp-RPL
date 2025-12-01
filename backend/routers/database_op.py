from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import backend.models as models, backend.schemas as schemas
from backend.database import SessionLocal, engine, get_db

models.Base.metadata.create_all(bind=engine)

router = APIRouter()

# ==============================================================
#   CUSTOMER CRUD
# ==============================================================

@router.post("/customer", response_model=schemas.Customer)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    new = models.Customer(**customer.dict())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


@router.get("/customer", response_model=list[schemas.Customer])
def get_customers(db: Session = Depends(get_db)):
    return db.query(models.Customer).all()


@router.put("/customer/{id_customer}", response_model=schemas.Customer)
def update_customer(id_customer: int, data: schemas.CustomerCreate, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id_customer == id_customer).first()
    if not customer:
        raise HTTPException(404, "Customer not found")

    for key, value in data.dict().items():
        setattr(customer, key, value)

    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/customer/{id_customer}")
def delete_customer(id_customer: int, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id_customer == id_customer).first()
    if not customer:
        raise HTTPException(404, "Customer not found")

    db.delete(customer)
    db.commit()
    return {"message": "Customer deleted successfully"}


# ==============================================================
#   ADMIN CRUD
# ==============================================================

@router.post("/admin", response_model=schemas.Admin)
def create_admin(admin: schemas.AdminCreate, db: Session = Depends(get_db)):
    new = models.Admin(**admin.dict())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


@router.get("/admin", response_model=list[schemas.Admin])
def get_admin(db: Session = Depends(get_db)):
    return db.query(models.Admin).all()


@router.put("/admin/{id_admin}", response_model=schemas.Admin)
def update_admin(id_admin: int, data: schemas.AdminCreate, db: Session = Depends(get_db)):
    admin = db.query(models.Admin).filter(models.Admin.id_admin == id_admin).first()
    if not admin:
        raise HTTPException(404, "Admin not found")

    for key, value in data.dict().items():
        setattr(admin, key, value)

    db.commit()
    db.refresh(admin)
    return admin


@router.delete("/admin/{id_admin}")
def delete_admin(id_admin: int, db: Session = Depends(get_db)):
    admin = db.query(models.Admin).filter(models.Admin.id_admin == id_admin).first()
    if not admin:
        raise HTTPException(404, "Admin not found")

    db.delete(admin)
    db.commit()
    return {"message": "Admin deleted successfully"}


# ==============================================================
#   MIKROKONTROLER CRUD
# ==============================================================

@router.post("/mikrokontroler", response_model=schemas.Mikrokontroler)
def create_mikrokontroler(db: Session = Depends(get_db)):
    new = models.Mikrokontroler()
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


@router.get("/mikrokontroler", response_model=list[schemas.Mikrokontroler])
def get_mikrokontroler(db: Session = Depends(get_db)):
    return db.query(models.Mikrokontroler).all()


@router.delete("/mikrokontroler/{id_mikrokontroler}")
def delete_mikrokontroler(id_mikrokontroler: int, db: Session = Depends(get_db)):
    mc = db.query(models.Mikrokontroler).filter(models.Mikrokontroler.id_mikrokontroler == id_mikrokontroler).first()
    if not mc:
        raise HTTPException(404, "Mikrokontroler not found")

    db.delete(mc)
    db.commit()
    return {"message": "Mikrokontroler deleted successfully"}


# ==============================================================
#   SLOT CRUD
# ==============================================================

@router.post("/slot", response_model=schemas.Slot)
def create_slot(slot: schemas.SlotCreate, db: Session = Depends(get_db)):
    # cek foreign key
    mc = db.query(models.Mikrokontroler).filter(
        models.Mikrokontroler.id_mikrokontroler == slot.id_mikrokontroler
    ).first()

    if not mc:
        raise HTTPException(404, "Mikrokontroler not found")

    new = models.Slot(**slot.dict())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


@router.get("/slot", response_model=list[schemas.Slot])
def get_slot(db: Session = Depends(get_db)):
    return db.query(models.Slot).all()

@router.put("/slot/{id_slot}", response_model=schemas.Slot)
def update_slot(id_slot: int, data: schemas.SlotCreate, db: Session = Depends(get_db)):
    slot = db.query(models.Slot).filter(models.Slot.id_slot == id_slot).first()
    if not slot:
        raise HTTPException(404, "Slot not found")

    # cek mikrokontroler jika ingin diupdate
    mc = db.query(models.Mikrokontroler).filter(
        models.Mikrokontroler.id_mikrokontroler == data.id_mikrokontroler
    ).first()

    if not mc:
        raise HTTPException(404, "Mikrokontroler tidak ditemukan")

    # update semua field
    for key, value in data.dict().items():
        setattr(slot, key, value)

    db.commit()
    db.refresh(slot)
    return slot


@router.delete("/slot/{id_slot}")
def delete_slot(id_slot: int, db: Session = Depends(get_db)):
    slot = db.query(models.Slot).filter(models.Slot.id_slot == id_slot).first()
    if not slot:
        raise HTTPException(404, "Slot not found")

    db.delete(slot)
    db.commit()
    return {"message": "Slot deleted successfully"}


# ==============================================================
#   AKTUATOR CRUD
# ==============================================================

@router.post("/aktuator", response_model=schemas.Aktuator)
def create_aktuator(aktuator: schemas.AktuatorCreate, db: Session = Depends(get_db)):
    # cek foreign key
    mc = db.query(models.Mikrokontroler).filter(
        models.Mikrokontroler.id_mikrokontroler == aktuator.id_mikrokontroler
    ).first()

    if not mc:
        raise HTTPException(404, "Mikrokontroler not found")

    new = models.Aktuator(**aktuator.dict())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


@router.get("/aktuator", response_model=list[schemas.Aktuator])
def get_aktuator(db: Session = Depends(get_db)):
    return db.query(models.Aktuator).all()

@router.put("/aktuator/{id_aktuator}", response_model=schemas.Aktuator)
def update_aktuator(id_aktuator: int, data: schemas.AktuatorCreate, db: Session = Depends(get_db)):
    aktuator = db.query(models.Aktuator).filter(models.Aktuator.id_aktuator == id_aktuator).first()
    if not aktuator:
        raise HTTPException(404, "Aktuator not found")

    # cek FK mikrokontroler
    mc = db.query(models.Mikrokontroler).filter(
        models.Mikrokontroler.id_mikrokontroler == data.id_mikrokontroler
    ).first()

    if not mc:
        raise HTTPException(404, "Mikrokontroler tidak ditemukan")

    # update data
    for key, value in data.dict().items():
        setattr(aktuator, key, value)

    db.commit()
    db.refresh(aktuator)
    return aktuator


@router.delete("/aktuator/{id_aktuator}")
def delete_aktuator(id_aktuator: int, db: Session = Depends(get_db)):
    akt = db.query(models.Aktuator).filter(models.Aktuator.id_aktuator == id_aktuator).first()
    if not akt:
        raise HTTPException(404, "Aktuator not found")

    db.delete(akt)
    db.commit()
    return {"message": "Aktuator deleted successfully"}

# ==============================================================
#   BOOKING CRUD
# ==============================================================

@router.get("/booking", response_model=list[schemas.Booking])
def get_booking(db: Session = Depends(get_db)):
    return db.query(models.Booking).all()

@router.post("/booking", response_model=schemas.Booking)
def create_booking(data: schemas.BookingCreate, db: Session = Depends(get_db)):
    # cek foreign key parkir
    parkir = db.query(models.Mikrokontroler).filter(
        models.Mikrokontroler.id_mikrokontroler == data.id_parkir
    ).first()
    if not parkir:
        raise HTTPException(404, "Parkir (Mikrokontroler) tidak ditemukan")

    # cek foreign key customer
    customer = db.query(models.Customer).filter(
        models.Customer.id_customer == data.id_customer
    ).first()
    if not customer:
        raise HTTPException(404, "Customer tidak ditemukan")

    booking = models.Booking(**data.dict())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

@router.put("/booking/{id_booking}", response_model=schemas.Booking)
def update_booking(id_booking: int, data: schemas.BookingUpdate, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(
        models.Booking.id_booking == id_booking
    ).first()

    if not booking:
        raise HTTPException(404, "Booking tidak ditemukan")

    # cek id_parkir jika ingin diupdate
    if data.id_parkir is not None:
        parkir = db.query(models.Mikrokontroler).filter(
            models.Mikrokontroler.id_mikrokontroler == data.id_parkir
        ).first()
        if not parkir:
            raise HTTPException(404, "Parkir tidak ditemukan")
        booking.id_parkir = data.id_parkir

    # cek id_customer jika ingin diupdate
    if data.id_customer is not None:
        cust = db.query(models.Customer).filter(
            models.Customer.id_customer == data.id_customer
        ).first()
        if not cust:
            raise HTTPException(404, "Customer tidak ditemukan")
        booking.id_customer = data.id_customer

    # update status jika dikirim
    if data.status is not None:
        booking.status = data.status

    db.commit()
    db.refresh(booking)
    return booking

@router.delete("/booking/{id_booking}")
def delete_booking(id_booking: int, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(
        models.Booking.id_booking == id_booking
    ).first()

    if not booking:
        raise HTTPException(404, "Booking tidak ditemukan")

    db.delete(booking)
    db.commit()
    return {"message": "Booking deleted successfully"}