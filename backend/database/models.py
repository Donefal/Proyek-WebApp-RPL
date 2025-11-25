from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from database import Base


# ================================
# TABLE CUSTOMER
# ================================
class Customer(Base):
    __tablename__ = "customer"

    id_customer = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True)
    email = Column(String(100), unique=True)
    notelp = Column(Integer)      # penting! nomer hp pakai String
    saldo = Column(Integer)


# ================================
# TABLE MIKROKONTROLER
# ================================
class Mikrokontroler(Base):
    __tablename__ = "mikrokontroler"

    id_mikrokontroler = Column(Integer, primary_key=True, index=True)

    # relasi ke sensor & aktuator
    sensor = relationship("Sensor", back_populates="mikrokontroler")
    aktuator = relationship("Aktuator", back_populates="mikrokontroler")


# ================================
# TABLE SENSOR
# ================================
class Sensor(Base):
    __tablename__ = "sensor"

    id_sensor = Column(Integer, primary_key=True, index=True)
    id_mikrokontroler = Column(Integer,
                               ForeignKey("mikrokontroler.id_mikrokontroler", ondelete="CASCADE"))

    mikrokontroler = relationship("Mikrokontroler", back_populates="sensor")


# ================================
# TABLE AKTUATOR
# ================================
class Aktuator(Base):
    __tablename__ = "aktuator"

    id_aktuator = Column(Integer, primary_key=True, index=True)
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
    email = Column(String(100), unique=True)
    notelp = Column(Integer)

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