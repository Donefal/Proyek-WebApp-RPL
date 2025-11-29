from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

# This will store the latest data received from the ESP32
last_data_from_esp32 = {}

# ============================
#   ESP32 → Backend (POST)
# ============================
@router.post("/update")
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
@router.get("/instruction")
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