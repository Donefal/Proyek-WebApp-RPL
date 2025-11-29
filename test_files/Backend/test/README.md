# Prototype Testing

## Dependencies
`pip install fastapi pydantic uvicorn`
Gunakan pip show uvicorn dan copy path Uvicorn Path ke environment variable path

## Firmware file
Ada pada direktori `../../hardware/firmware/esp8266_1Sensor_test

## Runnning API ini
uvicorn fastAPI_esp8266:app --reload --host 0.0.0.0 --port 8000

## Testing Tanpa ESP
Copy ke terminal (gunakan localhost)

curl -Method POST http://127.0.0.1:8000/api/update-slot-status `
  -Headers @{ "Content-Type"="application/json" } `
  -Body '{"slot_id":1,"slot_number":1,"status":"TESTING BERHASIL"}'