from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import database_op, hardware, auth, parking, wallet, admin

app = FastAPI()
origins = [
    "http://localhost:8080",   # untuk development
    "http://localhost:8880",   # jika frontend lokal
    "https://web.parkingly.space",  # domain frontend produksi
]

# CORS Configuration - Allow all origins for cross-device access
# In production, restrict to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow all origins for development/cross-device access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
db_router = database_op.router
hw_router = hardware.router
auth_router = auth.router
parking_router = parking.router
wallet_router = wallet.router
admin_router = admin.router

app.include_router(db_router, prefix="/db")
app.include_router(hw_router, prefix="/hw")
app.include_router(auth_router, tags=["auth"])
app.include_router(parking_router, tags=["parking"])
app.include_router(wallet_router, tags=["wallet"])
app.include_router(admin_router, tags=["admin"])

@app.get("/")
def read_root():
    return {"message": "FastAPI is running!"}
