#include <WiFi.h>
#include <WiFiClientSecure.h>   // HTTPS
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// =====================================================
// WiFi Credentials
// =====================================================
const char* ssid     = "donivalojagobanget";
const char* password = "donivalo99";

// =====================================================
// API Endpoints (HTTPS - Cloudflare)
// =====================================================
String GET_URL  = "https://api.parkingly.space/hw/instruction";
String POST_URL = "https://api.parkingly.space/hw/update";
String POST_GATE_URL = "https://api.parkingly.space/hw/update-gate";

// =====================================================
// Structs
// =====================================================
struct Ultrasonic {
  int trig;
  int echo;
};

struct Buzzer {
  int pin;
};

// =====================================================
// Constants
// =====================================================
const int AMOUNT_OF_SLOTS = 2;

// Ultrasonic pins {trig, echo}
const Ultrasonic SENSOR_PINS[AMOUNT_OF_SLOTS] = {
  {19, 21},
  {16, 17}
};

// =====================================================
// Servo Gate
// =====================================================
Servo enterGate;
Servo exitGate;

const int ENTER_GATE_PIN = 23;
const int EXIT_GATE_PIN  = 22;

const int ENTER_OPEN  = 180;
const int ENTER_CLOSE = 90;

const int EXIT_OPEN   = 0;
const int EXIT_CLOSE  = 90;

// =====================================================
// Buzzers
// =====================================================
const Buzzer BUZZERS[AMOUNT_OF_SLOTS] = {
  {25},
  {26}
};

// =====================================================
// Global State
// =====================================================
bool occupied[AMOUNT_OF_SLOTS] = {false, false};
bool alarmed[AMOUNT_OF_SLOTS]  = {false, false};
unsigned long gateCloseTime[2] = {0, 0}; // Track when gate should be considered closed (index 0 = enter, 1 = exit)
const unsigned long GATE_CLOSE_DELAY = 2500; // 2.5 seconds after opening (2s open + 0.5s buffer)
bool gateNeedsUpdate[2] = {false, false}; // Track if gate status needs to be sent to backend (index 0 = enter, 1 = exit)

// =====================================================
// Ultrasonic Measurement
// =====================================================
float measureDistance(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);

  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);

  long duration = pulseIn(echo, HIGH, 30000);
  if (duration == 0) {
    Serial.println("[SENSOR] Timeout");
    return 999;
  }

  float distance = duration * 0.034 / 2;
  return distance;
}

// =====================================================
// Alarm
// =====================================================
void alert(int slot) {
  Serial.print("[ALARM] Slot ");
  Serial.println(slot + 1);

  tone(BUZZERS[slot].pin, 1000, 300);
  delay(50);
  noTone(BUZZERS[slot].pin);
}

bool isNeedToAlarm(int i, bool booked, bool confirmed) {
  if (!booked && occupied[i]) return true;
  if (booked && !confirmed && occupied[i]) return true;
  return false;
}

// =====================================================
// GET API (HTTPS)
// =====================================================
bool getFromAPI(JsonDocument &doc) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[GET] WiFi not connected");
    return false;
  }

  WiFiClientSecure client;
  client.setInsecure();   // WAJIB untuk Cloudflare SSL

  HTTPClient http;
  http.setTimeout(5000);
  http.begin(client, GET_URL);

  Serial.println("[GET] Requesting instruction...");
  int code = http.GET();

  Serial.print("[GET] HTTP Code: ");
  Serial.println(code);

  if (code != HTTP_CODE_OK) {
    Serial.println("[GET] Failed");
    http.end();
    return false;
  }

  String payload = http.getString();
  Serial.print("[GET] Payload: ");
  Serial.println(payload);

  deserializeJson(doc, payload);
  http.end();
  return true;
}

// =====================================================
// POST API (HTTPS) - Slot Updates
// =====================================================
void sendToAPI() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[POST] WiFi not connected");
    return;
  }

  StaticJsonDocument<512> doc;
  JsonArray arr = doc.createNestedArray("slots");

  for (int i = 0; i < AMOUNT_OF_SLOTS; i++) {
    JsonObject slot = arr.createNestedObject();
    slot["id_slot"]  = i + 1;
    slot["occupied"] = occupied[i];
    slot["alarmed"]  = alarmed[i];
  }

  String json;
  serializeJson(doc, json);

  Serial.print("[POST] JSON: ");
  Serial.println(json);

  WiFiClientSecure client;
  client.setInsecure();

  HTTPClient http;
  http.setTimeout(5000);
  http.begin(client, POST_URL);
  http.addHeader("Content-Type", "application/json");

  int code = http.POST(json);
  Serial.print("[POST] HTTP Code: ");
  Serial.println(code);

  http.end();
}

// =====================================================
// POST API (HTTPS) - Gate Status Updates
// =====================================================
void sendGateStatusToAPI(int gateId, const char* condition) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[POST-GATE] WiFi not connected");
    return;
  }

  StaticJsonDocument<256> doc;
  JsonArray gates = doc.createNestedArray("gates");
  JsonObject gate = gates.createNestedObject();
  gate["id_gate"] = gateId;
  gate["condition"] = condition;

  String json;
  serializeJson(doc, json);

  Serial.print("[POST-GATE] JSON: ");
  Serial.println(json);

  WiFiClientSecure client;
  client.setInsecure();

  HTTPClient http;
  http.setTimeout(5000);
  http.begin(client, POST_GATE_URL);
  http.addHeader("Content-Type", "application/json");

  int code = http.POST(json);
  Serial.print("[POST-GATE] HTTP Code: ");
  Serial.println(code);

  http.end();
}

// =====================================================
// Gate Control
// =====================================================
bool gateOpening[2] = {false, false}; // Track if gate is currently opening (index 0 = enter, 1 = exit)

void openGate(Servo &gate, int open, int close, int gateId) {
  Serial.println("[GATE] Open");
  gate.write(open);
  gateOpening[gateId - 1] = true; // Mark gate as opening (gateId 1 = enter, 2 = exit)
  gateCloseTime[gateId - 1] = millis() + GATE_CLOSE_DELAY; // Set time when gate should be considered closed
  delay(2000);
  gate.write(close);
  gateOpening[gateId - 1] = false; // Mark gate as closed after operation
  gateNeedsUpdate[gateId - 1] = true; // Mark that gate status needs to be sent to backend
}

void closeGate(Servo &gate, int close) {
  Serial.println("[GATE] Close");
  gate.write(close);
}

// =====================================================
// Setup
// =====================================================
void setup() {
  Serial.begin(115200);
  Serial.println("\n=== ESP32 PARKINGLY START ===");

  // Buzzer & Sensor pin setup
  for (int i = 0; i < AMOUNT_OF_SLOTS; i++) {
    pinMode(BUZZERS[i].pin, OUTPUT);
    pinMode(SENSOR_PINS[i].trig, OUTPUT);
    pinMode(SENSOR_PINS[i].echo, INPUT);
  }

  // Servo attach
  enterGate.attach(ENTER_GATE_PIN, 500, 2500);
  exitGate.attach(EXIT_GATE_PIN, 500, 2500);

  // WiFi connect
  Serial.print("[WiFi] Connecting");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  closeGate(exitGate, EXIT_CLOSE);
  closeGate(enterGate, ENTER_CLOSE);

  Serial.println("\n[WiFi] Connected");
  Serial.print("[WiFi] IP: ");
  Serial.println(WiFi.localIP());
}

// =====================================================
// Loop
// =====================================================
void loop() {
  // ===== Sensor Reading =====
  for (int i = 0; i < AMOUNT_OF_SLOTS; i++) {
    float dist = measureDistance(SENSOR_PINS[i].trig, SENSOR_PINS[i].echo);
    occupied[i] = (dist < 5);

    Serial.print("[SENSOR] Slot ");
    Serial.print(i + 1);
    Serial.print(" | Distance: ");
    Serial.print(dist);
    Serial.print(" cm | Occupied: ");
    Serial.println(occupied[i]);
  }

  // ===== GET instruction =====
  StaticJsonDocument<512> apiResponse;
  if (getFromAPI(apiResponse)) {

    JsonArray slots = apiResponse["slots"];
    JsonArray gates = apiResponse["gates"];

    // Slot logic
    for (JsonObject slot : slots) {
      int index = slot["id_slot"].as<int>() - 1;
      if (index < 0 || index >= AMOUNT_OF_SLOTS) continue;

      bool booked    = slot["booked"];
      bool confirmed = slot["confirmed"];

      Serial.printf("[API] Slot %d | booked:%d confirmed:%d\n", index + 1, booked, confirmed);

      alarmed[index] = isNeedToAlarm(index, booked, confirmed);
      if (alarmed[index]) alert(index);
    }

    // Gate logic - only open if buka is true and gate is not already opening
    for (JsonObject gate : gates) {
      int id   = gate["id_aktuator"];
      bool buka = gate["buka"];

      Serial.printf("[API] Gate %d | buka:%d\n", id, buka);

      // Only open gate if buka is true and gate is not currently opening
      // This prevents multiple simultaneous gate operations
      if (id == 1 && buka && !gateOpening[0]) {
        openGate(enterGate, ENTER_OPEN, ENTER_CLOSE, 1);
      }
      if (id == 2 && buka && !gateOpening[1]) {
        openGate(exitGate, EXIT_OPEN, EXIT_CLOSE, 2);
      }
    }
  } else {
    Serial.println("[API] is not okay");
  }

  // ===== POST status =====
  sendToAPI();
  
  // Send gate status updates after gate operations complete
  // This allows backend to reset kondisi_buka after hardware confirms gate closed
  for (int i = 0; i < 2; i++) {
    if (gateNeedsUpdate[i] && !gateOpening[i]) {
      // Gate operation completed, send status update to backend
      int gateId = i + 1; // Convert index to gate ID (1 = enter, 2 = exit)
      sendGateStatusToAPI(gateId, "closed");
      gateNeedsUpdate[i] = false; // Mark as sent
    }
  }

  Serial.println("=================================");
  delay(3000);
}