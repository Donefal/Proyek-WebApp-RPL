#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// =======================
// WiFi Credentials
// =======================
const char* ssid = "realme 8i";
const char* password = "avinavin";

// =======================
// API Endpoints
// =======================
String GET_URL = "http://10.154.169.209:8000/hw/instruction";
String POST_URL = "http://10.154.169.209:8000/hw/update";

// =======================
// Structs
// =======================
struct Ultrasonic {
  int trig;
  int echo;
};

struct Buzzer {
  int pin;
};

// =======================
// Constants
// =======================
const int AMOUNT_OF_SLOTS = 2;

// {Trig, echo}
const Ultrasonic SENSOR_PINS[AMOUNT_OF_SLOTS] = {
  {19, 21},
  {16, 17}
};

// Servos
Servo enterGate;
Servo exitGate;

const int ENTER_GATE_PIN = 13;
const int EXIT_GATE_PIN  = 14;

// Buzzers
const Buzzer BUZZERS[AMOUNT_OF_SLOTS] = {
  {25},
  {26}
};

// =======================
// Global State
// =======================
bool occupied[AMOUNT_OF_SLOTS] = {false, false};
bool alarmed[AMOUNT_OF_SLOTS]  = {false, false};

// =======================
// Ultrasonic
// =======================
float measureDistance(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);

  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);

  long duration = pulseIn(echo, HIGH, 30000);
  if(duration == 0) return 999;

  float distance = duration * 0.034 / 2;

  Serial.printf("Distance: %.2f, ", distance);
  return distance;
}

// =======================
// Alarm
// =======================
void alert(int slot) {
  int pin = BUZZERS[slot].pin;
  tone(pin, 1000, 300);
  delay(50);
  noTone(pin);
}

bool isNeedToAlarm(int i, bool booked, bool confirmed) {
  if(!booked && occupied[i]) return true;
  if(booked && !confirmed && occupied[i]) return true;
  return false;
}

// =======================
// GET API
// =======================
bool getFromAPI(JsonDocument &doc) {
  if (WiFi.status() != WL_CONNECTED) return false;

  HTTPClient http;
  http.begin(GET_URL);

  int code = http.GET();
  Serial.print("GET Response: ");
  Serial.println(code);

  if (code != 200) {
    http.end();
    return false;
  }

  deserializeJson(doc, http.getString());
  http.end();
  return true;
}

// =======================
// POST API
// =======================
void sendToAPI() {
  if (WiFi.status() != WL_CONNECTED) return;

  StaticJsonDocument<512> doc;
  JsonArray arr = doc.createNestedArray("slots");

  for (int i = 0; i < AMOUNT_OF_SLOTS; i++) {
    JsonObject slot = arr.createNestedObject();
    slot["id_slot"] = i + 1;
    slot["occupied"] = occupied[i];
    slot["alarmed"] = alarmed[i];
  }

  String json;
  serializeJson(doc, json);

  HTTPClient http;
  http.begin(POST_URL);
  http.addHeader("Content-Type", "application/json");

  int code = http.POST(json);
  Serial.print("POST Response: ");
  Serial.println(code);

  http.end();
}

// =======================
// Gate Control
// =======================
void openGate(Servo &gate) {
  gate.write(90);
  delay(2000);
  gate.write(0);
}

// =======================
// SETUP
// =======================
void setup() {
  Serial.begin(115200);

  // Buzzer pins
  for (int i = 0; i < AMOUNT_OF_SLOTS; i++) {
    pinMode(BUZZERS[i].pin, OUTPUT);
  }

  // Ultrasonic pins
  for (int i = 0; i < AMOUNT_OF_SLOTS; i++) {
    pinMode(SENSOR_PINS[i].trig, OUTPUT);
    pinMode(SENSOR_PINS[i].echo, INPUT);
  }

  enterGate.attach(ENTER_GATE_PIN);
  exitGate.attach(EXIT_GATE_PIN);

  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }

  Serial.println("\nConnected!");
  Serial.println(WiFi.localIP());
}

// =======================
// LOOP
// =======================
void loop() {
  // 1. Ultrasonic sensing
  for (int i = 0; i < AMOUNT_OF_SLOTS; i++) {
    float dist = measureDistance(SENSOR_PINS[i].trig, SENSOR_PINS[i].echo);
    occupied[i] = (dist < 10);
    Serial.print(occupied[i]);
    Serial.print(" | ");
  }
  Serial.println();

  StaticJsonDocument<512> apiResponse;
  bool ok = getFromAPI(apiResponse);

  if (ok) {
    JsonArray slots = apiResponse["slots"].as<JsonArray>();
    JsonArray gates = apiResponse["gates"].as<JsonArray>();

    // Slot logic
    for (JsonObject slot : slots) {
      int id = slot["id_slot"];
      bool booked = slot["booked"];
      bool confirmed = slot["confirmed"];

      int index = id - 1;
      if (index < 0 || index >= AMOUNT_OF_SLOTS) continue;

      alarmed[index] = isNeedToAlarm(index, booked, confirmed);
      if (alarmed[index]) alert(index);
    }

    // Gate logic
    for (JsonObject gate : gates) {
      int id = gate["id_aktuator"];
      bool buka = gate["buka"];

      if (buka) {
        if (id == 0) openGate(enterGate);
        else if (id == 1) openGate(exitGate);
        else {
          Serial.print("Invalid gate actuator: ");
          Serial.println(id);
        }
      }
    }
  }

  sendToAPI();
  delay(2000);
}
