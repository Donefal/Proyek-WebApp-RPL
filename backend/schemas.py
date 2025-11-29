import datetime
from pydantic import BaseModel
from typing import Optional, List


# ======================================================
# CUSTOMER
# ======================================================

class CustomerBase(BaseModel):
    username: str
    email: str
    notelp: str
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
    notelp: str


class AdminCreate(AdminBase):
    pass


class Admin(AdminBase):
    id_admin: int

    class Config:
        orm_mode = True


# ======================================================
# SLOT
# ======================================================

class SlotBase(BaseModel):
    id_mikrokontroler: int


class SlotCreate(SlotBase):
    pass


class Slot(BaseModel):
    id_slot: int
    booked: bool
    confirmed: bool
    occupied: bool
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
    nama_aktuator: bool
    kondisi: bool

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
# ------ Nested (include slot & actuators) ------
class Mikrokontroler(BaseModel):
    id_mikrokontroler: int

    # relasi (opsional)
    slot: Optional[List[Slot]] = []
    aktuator: Optional[List[Aktuator]] = []

    class Config:
        orm_mode = True
