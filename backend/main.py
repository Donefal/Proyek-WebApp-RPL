from fastapi import FastAPI
from routers.database_op import router as db_router
from routers.hardware import router as hw_router

app = FastAPI()

app.include_router(db_router, prefix="/db")
app.include_router(hw_router, prefix="/hw")

@app.get("/")
def read_root():
    return {"message": "FastAPI is running!"}
