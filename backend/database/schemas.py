import datetime
from pydantic import BaseModel
from typing import Optional, List


# ======================================================
# CUSTOMER
# ======================================================

class CustomerBase(BaseModel):
    username: str
    email: str
    notelp: int
    saldo: Optional[int] = 0


class CustomerCreate(CustomerBase):
    pass


class Customer(CustomerBase):
    id_customer: int

    class Config:
        orm_mode = True


# ======================================================
# ADMIN
# ======================================================

class AdminBase(BaseModel):
    username: str
    email: str
    notelp: int


class AdminCreate(AdminBase):
    pass


class Admin(AdminBase):
    id_admin: int

    class Config:
        orm_mode = True


# ======================================================
# SENSOR
# ======================================================

class SensorBase(BaseModel):
    id_mikrokontroler: int


class SensorCreate(SensorBase):
    pass


class Sensor(BaseModel):
    id_sensor: int
    id_mikrokontroler: int

    class Config:
        orm_mode = True


# ======================================================
# AKTUATOR
# ======================================================

class AktuatorBase(BaseModel):
    id_mikrokontroler: int


class AktuatorCreate(AktuatorBase):
    pass


class Aktuator(BaseModel):
    id_aktuator: int
    id_mikrokontroler: int

    class Config:
        orm_mode = True


# ======================================================
# MIKROKONTROLER
# ======================================================

class MikrokontrolerBase(BaseModel):
    pass


class MikrokontrolerCreate(MikrokontrolerBase):
    pass

# ======================================================
# BOOKING
# ======================================================

class BookingBase(BaseModel):
    id_parkir: int
    id_customer: int

class BookingCreate(BookingBase):
    pass

class Booking(BookingBase):
    id_booking: int
    waktu_booking: datetime.datetime
    waktu_masuk: datetime.datetime | None
    waktu_keluar: datetime.datetime | None
    status: str

class BookingUpdate(BaseModel):
    id_parkir: int | None = None
    id_customer: int | None = None
    status: str | None = None

    class Config:
        orm_mode = True
# ------ Nested (include sensors & actuators) ------
class Mikrokontroler(BaseModel):
    id_mikrokontroler: int

    # relasi (opsional)
    sensor: Optional[List[Sensor]] = []
    aktuator: Optional[List[Aktuator]] = []

    class Config:
        orm_mode = True
