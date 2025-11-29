from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.database import get_db
import models, schemas

router = APIRouter()

# ============================
#   ESP32 → Backend (POST)
# ============================
@router.post("/update")
async def update_from_esp32(data: schemas.FromESP32, db: Session = Depends(get_db)):
    print("Received from ESP32:", data.dict())

    # TODO: Connect to database and update it

    return {"status": "OK", "saved_slot": len(data.slots)}


# ============================
#   Backend → ESP32 (GET)
# ============================
@router.get("/instruction")
def send_instruction_to_esp32(db: Session = Depends(get_db)):
    slots = db.query(models.Slot).all()

    # TODO: pull data from database (slots) and put on this variable (kyk fungsi dibawahnya)
    gates = []
    slots = []

    return schemas.ToESP32(gates=gates, slots=slots)


@router.get("/instruction-test")
def send_instruction_to_esp32_test():
    # Example instruction the ESP32 can read
    gates = [
        {"nama_aktuator": "enterGate", "buka" : True},
		{"nama_aktuator": "exitGate", "buka" : True}
    ]

    slots = [
        {"id_slot": 1, "booked": True, "confirmed": False},
        {"id_slot": 2, "booked": True, "confirmed": True},
    ]

    return schemas.ToESP32(gates=gates, slots=slots)
    