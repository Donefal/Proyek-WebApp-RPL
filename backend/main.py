from fastapi import FastAPI
from backend.routers import database_op, hardware

app = FastAPI()

db_router = database_op.router
hw_router = hardware.router

app.include_router(db_router, prefix="/db")
app.include_router(hw_router, prefix="/hw")

@app.get("/")
def read_root():
    return {"message": "FastAPI is running!"}
