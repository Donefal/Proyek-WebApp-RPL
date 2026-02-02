from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_USER = "web"
DB_PASSWORD = ""     # atau password MySQL kamu
DB_HOST = "192.168.4.13"
DB_PORT = "3306"
DB_NAME = "fastapi_db"

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ===============================
# FastAPI dependency (untuk Depends())
# ===============================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()