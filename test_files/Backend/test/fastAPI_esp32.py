# Run: fastapi dev fastAPI_esp32:app --host 0.0.0.0 --port 8000
""" 
TODO: 
    Coba dari .post datanya diteruskan kembali ke @app.post ke endpoint db
    Nah dari situ coba di format dulu supaya sesuai sama databasenya.
"""

from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse

app = FastAPI()

# This will store the latest data received from the ESP32
last_data_from_esp32 = {}

@app.get("/")
def read_root():
    return {"message": "FastAPI is running!"}


# ============================
#   ESP32 → Backend (POST)
# ============================
@app.post("/hw/update")
async def update_from_esp32(request: Request):
    global last_data_from_esp32

    # Parse incoming JSON
    data = await request.json()

    # Save it (for testing)
    last_data_from_esp32 = data

    print("Received from ESP32:", data)

    return {"status": "OK", "received": data}


# ============================
#   Backend → ESP32 (GET)
# ============================
@app.get("/hw/instruction")
def send_instruction_to_esp32():
    # Example instruction the ESP32 can read
    instruction = {
        "enterShouldOpen": False,
        "exitShouldOpen": False,
        "slots": [
            {"no": 1, "booked": False, "confirmed": False},
            {"no": 2, "booked": False, "confirmed": False},
            {"no": 3, "booked": False, "confirmed": False}
        ]}

    return JSONResponse(content=instruction)
