"""
--- Install dependencies
`pip install fastapi pydantic uvicorn`
Gunakan pip show uvicorn dan copy path Uvicorn Path ke environment variable path

--- Runnning API ini
uvicorn fastAPI_esp8266:app --reload --host 0.0.0.0 --port 8000

--- Testing Tanpa ESP
Copy ke terminal (gunakan localhost)

curl -Method POST http://127.0.0.1:8000/api/update-slot-status `
  -Headers @{ "Content-Type"="application/json" } `
  -Body '{"slot_id":1,"slot_number":1,"status":"TESTING BERHASIL"}'
"""

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
    print("Received data:", data.dict())   # prints ke terminal
    return {
        "message": "Data received successfully",
        "received": data.dict()
    }  
