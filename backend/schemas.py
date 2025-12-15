import datetime
from pydantic import BaseModel
from typing import Optional, List


# ======================================================
# CUSTOMER
# ======================================================

class CustomerBase(BaseModel):
    username: str
    password: str
    email: str
    notelp: str
    saldo: Optional[int] = 0


class CustomerCreate(CustomerBase):
    pass


class Customer(CustomerBase):
    id_customer: int

    class Config:
        from_attributes = True


# ======================================================
# AUTHENTICATION
# ======================================================

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    notelp: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ======================================================
# ADMIN
# ======================================================

class AdminBase(BaseModel):
    username: str
    password: str
    email: str
    notelp: str


class AdminCreate(AdminBase):
    pass


class Admin(AdminBase):
    id_admin: int

    class Config:
        from_attributes = True


# ======================================================
# SLOT
# ======================================================

class SlotBase(BaseModel):
    id_mikrokontroler: int


class SlotCreate(SlotBase):
    # optional flags for initial state — default to False if omitted by client
    booked: bool = False
    confirmed: bool = False
    occupied: bool = False
    alarmed: bool = False


class Slot(BaseModel):
    id_slot: int
    booked: bool = False # Slot di booking
    confirmed: bool = False # Slot sdh dikonfirmasi (true bila sudah scan)
    occupied: bool = False # Slot sedang ada mobilnya
    alarmed: bool = False # Slot yg belum confirm tapi sdh occupied (alarm bunyi)

    class Config:
        from_attributes = True


# ======================================================
# AKTUATOR
# ======================================================

class AktuatorBase(BaseModel):
    id_mikrokontroler: int


class AktuatorCreate(AktuatorBase):
    pass


class Aktuator(BaseModel):
    id_aktuator: int
    nama_aktuator: str
    usable: bool
    kondisi_buka: bool
    aksi_gate: str

    class Config:
        from_attributes = True


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
        from_attributes = True
# ------ Nested (include slot & actuators) ------
class Mikrokontroler(BaseModel):
    id_mikrokontroler: int

    # relasi (opsional)
    slot: Optional[List[Slot]] = []
    aktuator: Optional[List[Aktuator]] = []

    class Config:
        from_attributes = True


# ======================================================
# ESP32 HARDWARE DATA
# ======================================================

# ESP32 -> API -------------------------------
class SlotDetection(BaseModel):
    id_slot: int
    occupied: bool # Slot sedang ada mobilnya
    alarmed: bool # Slot yg belum confirm tapi sdh occupied (alarm bunyi)

class GateCondition(BaseModel):
    id_gate: int
    condition: str

class FromESP32_detection(BaseModel):
    slots: list[SlotDetection]

class FromESP33_gate(BaseModel):
    gates: list[GateCondition]

# API -> ESP32 -------------------------------
class SlotData(BaseModel):
    id_slot: int
    booked: bool
    confirmed: bool

class GateData(BaseModel):
    id_aktuator: int
    buka: bool
    
class ToESP32(BaseModel):
    slots: list[SlotData]
    gates: list[GateData]
