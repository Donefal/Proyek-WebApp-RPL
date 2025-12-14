#include <WiFi.h>
#include <WiFiClientSecure.h>   // HTTPS
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// =====================================================
// WiFi Credentials
// =====================================================
const char* ssid     = "DihKoqAku";
const char* password = "BocilTuyul30";

// =====================================================
// API Endpoints (HTTPS - Cloudflare)
// =====================================================
String GET_URL  = "https://api.parkingly.space/hw/instruction";
String POST_URL = "https://api.parkingly.space/hw/update";

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
// POST API (HTTPS)
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
// Gate Control
// =====================================================
void openGate(Servo &gate, int open, int close) {
  Serial.println("[GATE] Open");
  gate.write(open);
  delay(2000);
  gate.write(close);
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

    // Gate logic
    for (JsonObject gate : gates) {
      int id   = gate["id_aktuator"];
      bool buka = gate["buka"];

      Serial.printf("[API] Gate %d | buka:%d\n", id, buka);

      if (id == 1 && buka) openGate(enterGate, ENTER_OPEN, ENTER_CLOSE);
      if (id == 2 && buka) openGate(exitGate, EXIT_OPEN, EXIT_CLOSE);
    }
  } else {
    Serial.println("[API] is not okay");
  }

  // ===== POST status =====
  sendToAPI();

  Serial.println("=================================");
  delay(3000);
}