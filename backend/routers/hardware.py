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

    # TODO: Testing data
    for slot_update in data.slots:
        slot = db.query(models.Slot).filter(models.Slot.id_slot == slot_update.id_slot).first()
        if slot:
            slot.occupied = slot_update.occupied
            slot.calculated = slot_update.calculated

    db.commit()

    return {"status": "OK", "saved_slot": len(data.slots)}


# ============================
#   Backend → ESP32 (GET)
# ============================
@router.get("/instruction", response_model=schemas.ToESP32)
def send_instruction_to_esp32(db: Session = Depends(get_db)):
    # TODO: Testing data
    db_slots = db.query(models.Slot).all()
    slots = [
        schemas.SlotData(
            id_slot= slot.id_slot,
            booked= slot.booked,
            confirmed= slot.confirmed
        )
        for slot in db_slots 
    ]

    # Hanya mengambil aktuator yang usable
    db_gates = db.query(models.Aktuator).filter(models.Aktuator.usable == True).all()
    gates = [
        schemas.GateData(
            id_aktuator= gate.id_aktuator,
            buka= True # TODO: Ini harus sesuai dengan kondisi sesungguhnya
        )
        for gate in db_gates
    ]

    return schemas.ToESP32(slots=slots, gates=gates)


@router.get("/instruction-test", response_model=schemas.ToESP32)
def send_instruction_to_esp32_test():
    # Example instruction the ESP32 can read
    gates = [
        {"nama_aktuator": "enterGate", "buka" : True},
		{"nama_aktuator": "exitGate", "buka" : True}
    ]

    slots = [
        {"id_slot": 1, "booked": True, "confirmed": False}, # Uji kondisi alarmed = true
        {"id_slot": 2, "booked": True, "confirmed": True}, # Uji kondisi alarmed = false
    ]

    return schemas.ToESP32(gates=gates, slots=slots)
    