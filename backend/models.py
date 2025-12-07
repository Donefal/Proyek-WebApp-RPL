from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
import datetime
from backend.database import Base


# ================================
# TABLE CUSTOMER
# ================================
class Customer(Base):
    __tablename__ = "customer"

    id_customer = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True)
    password = Column(String(100))
    email = Column(String(100), unique=True)
    notelp = Column(String (16))     
    saldo = Column(Integer)


# ================================
# TABLE MIKROKONTROLER
# ================================
class Mikrokontroler(Base):
    __tablename__ = "mikrokontroler"

    id_mikrokontroler = Column(Integer, primary_key=True, index=True)

    # relasi ke slot & aktuator
    slot = relationship("Slot", back_populates="mikrokontroler")
    aktuator = relationship("Aktuator", back_populates="mikrokontroler")


# ================================
# TABLE SLOT
# ================================
class Slot(Base):
    __tablename__ = "slot_condition"

    id_slot = Column(Integer, primary_key=True, index=True)
    booked = Column(Boolean, default=False, nullable=False) # Slot di booking
    confirmed = Column(Boolean, default=False, nullable=False) # Slot sdh dikonfirmasi (true bila sudah scan)
    occupied = Column(Boolean, default=False, nullable=False) # Slot sedang ada mobilnya
    alarmed = Column(Boolean, default=False, nullable=False) # Slot yg belum confirm tapi sdh occupied (alarm bunyi)
    id_mikrokontroler = Column(Integer,
                               ForeignKey("mikrokontroler.id_mikrokontroler", ondelete="CASCADE"))

    mikrokontroler = relationship("Mikrokontroler", back_populates="slot")


# ================================
# TABLE AKTUATOR
# ================================
class Aktuator(Base):
    __tablename__ = "aktuator"

    id_aktuator = Column(Integer, primary_key=True, index=True)
    nama_aktuator = Column(String(100))
    usable = Column(Boolean)
    id_mikrokontroler = Column(Integer,
                               ForeignKey("mikrokontroler.id_mikrokontroler", ondelete="CASCADE"))

    mikrokontroler = relationship("Mikrokontroler", back_populates="aktuator")


# ================================
# TABLE ADMIN
# ================================
class Admin(Base):
    __tablename__ = "admin"

    id_admin = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True)
    password = Column(String(100))
    email = Column(String(100), unique=True)
    notelp = Column(String(16))

# ==========================
# BOOKING TABLE
# ==========================
class Booking(Base):
    __tablename__ = "booking"

    id_booking = Column(Integer, primary_key=True, index=True)
    
    id_parkir = Column(Integer, ForeignKey("mikrokontroler.id_mikrokontroler"))
    id_customer = Column(Integer, ForeignKey("customer.id_customer"))

    waktu_booking = Column(DateTime, default=datetime.datetime.utcnow)
    waktu_masuk = Column(DateTime, nullable=True)
    waktu_keluar = Column(DateTime, nullable=True)

    status = Column(String(20), default="pending")

    # Relasi
    customer = relationship("Customer")
    parkir = relationship("Mikrokontroler")