from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_USER = "root"
DB_PASSWORD = ""     # atau password MySQL kamu
DB_HOST = "127.0.0.1"
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