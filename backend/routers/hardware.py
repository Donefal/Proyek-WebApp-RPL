from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.database import get_db
import backend.models as models, backend.schemas as schemas

router = APIRouter()

# ============================
#   ESP32 → Backend (POST)
# ============================
@router.post("/update")
async def update_from_esp32(data: schemas.FromESP32_detection, db: Session = Depends(get_db)):
    print("(Slot) Received from ESP32:", data.dict())

    for slot_update in data.slots:
        slot = db.query(models.Slot).filter(models.Slot.id_slot == slot_update.id_slot).first()
        if slot:
            slot.occupied = slot_update.occupied
            slot.alarmed = slot_update.alarmed
    
    # Only reset gates that were opened by hardware (not by frontend)
    # Frontend sets kondisi_buka to True, hardware should only reset it after gate operation completes
    # We don't reset gates here anymore - let hardware send gate status via update-gate endpoint
    # This prevents race condition where frontend sets gate to open but hardware resets it before gate opens

    db.commit()

    return {"status": "OK", "saved_slot": len(data.slots)}

@router.post("/update-gate")
async def update_gate_from_esp32(data: schemas.FromESP33_gate, db: Session = Depends(get_db)):
    print("(Gate) Received from ESP32:", data.dict())

    for gate_update in data.gates:
        gate = db.query(models.Aktuator).filter(models.Aktuator.id_aktuator == gate_update.id_gate).first()

        if gate:
            gate.aksi_gate = gate_update.condition
            # Reset kondisi_buka to False only after hardware confirms gate operation completed
            # This allows frontend commands to have priority and gate stays open until hardware confirms closure
            if gate_update.condition == "closed":
                gate.kondisi_buka = False

    db.commit()
    return {"status": "OK", "saved_gates": len(data.gates)}

# ============================
#   Backend → ESP32 (GET)
# ============================
@router.get("/instruction", response_model=schemas.ToESP32)
def send_instruction_to_esp32(db: Session = Depends(get_db)):
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
            buka= gate.kondisi_buka  # Mengambil kondisi_buka dari database
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
    