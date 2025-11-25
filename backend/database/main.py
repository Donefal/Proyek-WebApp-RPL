from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

import models, schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# ==============================================================
#   DATABASE SESSION
# ==============================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==============================================================
#   CUSTOMER CRUD
# ==============================================================

@app.post("/dbcustomer", response_model=schemas.Customer)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    new = models.Customer(**customer.dict())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


@app.get("/dbcustomer", response_model=list[schemas.Customer])
def get_customers(db: Session = Depends(get_db)):
    return db.query(models.Customer).all()


@app.put("/dbcustomer/{id_customer}", response_model=schemas.Customer)
def update_customer(id_customer: int, data: schemas.CustomerCreate, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id_customer == id_customer).first()
    if not customer:
        raise HTTPException(404, "Customer not found")

    for key, value in data.dict().items():
        setattr(customer, key, value)

    db.commit()
    db.refresh(customer)
    return customer


@app.delete("/dbcustomer/{id_customer}")
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

@app.post("/dbadmin", response_model=schemas.Admin)
def create_admin(admin: schemas.AdminCreate, db: Session = Depends(get_db)):
    new = models.Admin(**admin.dict())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


@app.get("/dbadmin", response_model=list[schemas.Admin])
def get_admin(db: Session = Depends(get_db)):
    return db.query(models.Admin).all()


@app.put("/dbadmin/{id_admin}", response_model=schemas.Admin)
def update_admin(id_admin: int, data: schemas.AdminCreate, db: Session = Depends(get_db)):
    admin = db.query(models.Admin).filter(models.Admin.id_admin == id_admin).first()
    if not admin:
        raise HTTPException(404, "Admin not found")

    for key, value in data.dict().items():
        setattr(admin, key, value)

    db.commit()
    db.refresh(admin)
    return admin


@app.delete("/dbadmin/{id_admin}")
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

@app.post("/dbmikrokontroler", response_model=schemas.Mikrokontroler)
def create_mikrokontroler(db: Session = Depends(get_db)):
    new = models.Mikrokontroler()
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


@app.get("/dbmikrokontroler", response_model=list[schemas.Mikrokontroler])
def get_mikrokontroler(db: Session = Depends(get_db)):
    return db.query(models.Mikrokontroler).all()


@app.delete("/dbmikrokontroler/{id_mikrokontroler}")
def delete_mikrokontroler(id_mikrokontroler: int, db: Session = Depends(get_db)):
    mc = db.query(models.Mikrokontroler).filter(models.Mikrokontroler.id_mikrokontroler == id_mikrokontroler).first()
    if not mc:
        raise HTTPException(404, "Mikrokontroler not found")

    db.delete(mc)
    db.commit()
    return {"message": "Mikrokontroler deleted successfully"}


# ==============================================================
#   SENSOR CRUD
# ==============================================================

@app.post("/dbsensor", response_model=schemas.Sensor)
def create_sensor(sensor: schemas.SensorCreate, db: Session = Depends(get_db)):
    # cek foreign key
    mc = db.query(models.Mikrokontroler).filter(
        models.Mikrokontroler.id_mikrokontroler == sensor.id_mikrokontroler
    ).first()

    if not mc:
        raise HTTPException(404, "Mikrokontroler not found")

    new = models.Sensor(**sensor.dict())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


@app.get("/dbsensor", response_model=list[schemas.Sensor])
def get_sensor(db: Session = Depends(get_db)):
    return db.query(models.Sensor).all()


@app.delete("/dbsensor/{id_sensor}")
def delete_sensor(id_sensor: int, db: Session = Depends(get_db)):
    sensor = db.query(models.Sensor).filter(models.Sensor.id_sensor == id_sensor).first()
    if not sensor:
        raise HTTPException(404, "Sensor not found")

    db.delete(sensor)
    db.commit()
    return {"message": "Sensor deleted successfully"}


# ==============================================================
#   AKTUATOR CRUD
# ==============================================================

@app.post("/dbaktuator", response_model=schemas.Aktuator)
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


@app.get("/dbaktuator", response_model=list[schemas.Aktuator])
def get_aktuator(db: Session = Depends(get_db)):
    return db.query(models.Aktuator).all()


@app.delete("/dbaktuator/{id_aktuator}")
def delete_aktuator(id_aktuator: int, db: Session = Depends(get_db)):
    akt = db.query(models.Aktuator).filter(models.Aktuator.id_aktuator == id_aktuator).first()
    if not akt:
        raise HTTPException(404, "Aktuator not found")

    db.delete(akt)
    db.commit()
    return {"message": "Aktuator deleted successfully"}

@app.get("/dbbooking", response_model=list[schemas.Booking])
def get_booking(db: Session = Depends(get_db)):
    return db.query(models.Booking).all()

@app.post("/dbbooking", response_model=schemas.Booking)
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

@app.put("/dbbooking/{id_booking}", response_model=schemas.Booking)
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

@app.delete("/dbbooking/{id_booking}")
def delete_booking(id_booking: int, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(
        models.Booking.id_booking == id_booking
    ).first()

    if not booking:
        raise HTTPException(404, "Booking tidak ditemukan")

    db.delete(booking)
    db.commit()
    return {"message": "Booking deleted successfully"}