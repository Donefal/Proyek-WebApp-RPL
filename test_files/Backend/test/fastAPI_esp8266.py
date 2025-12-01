from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Model data
class SlotStatus(BaseModel):
    slot_id: int
    slot_number: int
    status: str

# API Endpoint
@app.post("/api/update-slot-status")
async def update_slot_status(data: SlotStatus):
    print("Received data:", data.model_dump())   # prints ke terminal
    return {
        "message": "Data received successfully",
        "received": data.dict()
    }  
