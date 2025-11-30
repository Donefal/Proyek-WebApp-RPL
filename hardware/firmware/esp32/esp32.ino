/*
  TODO: ROMBAK
  1. Implementasi send_instruction_to_esp32_test() dari hardware.py
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// =======================
// WiFi Credentials
// =======================
const char* ssid = "Az Zahra Living";
const char* password = "cibiruhilir15";

// =======================
// API Endpoints
// TODO: Apakah ada cara agar IP endpoint tidak hardcoded
// =======================
String GET_URL = "http://10.34.222.209:8000/hw/instruction";
String POST_URL = "http://10.34.222.209:8000/hw/update";

// =======================
// Struct Declaration
// =======================
struct Ultrasonic {
  int trig;
  int echo;
};

struct Buzzer {
  int pin;
}

// =======================
// Constants
// =======================
const int AMOUNT_OF_SLOTS = 2;

// TODO: Need to be hardcoded
const Ultrasonic SENSOR_PINS[AMOUNT_OF_SLOTS] = {
  {18, 19},   // slot 1
  {16, 17}  // slot 2
};

// Servos
Servo enterGate;
Servo exitGate;
const int ENTER_GATE_PIN = 13;
const int EXIT_GATE_PIN = 14;

// Buzzers
const Buzzer BUZZER_PIN[AMOUNT_OF_SLOTS] = {
  27, // slot 1
  28 // slot 2
}

// =======================
// Main Variable
// =======================
bool occupied[AMOUNT_OF_SLOTS];
for (int i = 0; i < AMOUNT_OF_SLOTS; i++){ occupied[i] = false; }

bool alarmed[AMOUNT_OF_SLOTS];
for (int i = 0; i < AMOUNT_OF_SLOTS; i++){ alarmed[i] = false; }

// =======================
// Helper Functions
// =======================
float measureDistance(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);

  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);

  long duration = pulseIn(echo, HIGH, 30000);
  float distance = duration * 0.034 / 2;

  Serial.print("Distance: ");
  Serial.println(distance);
  if (duration == 0) return 999;  
  return distance;
}

void alert(int slot) {
  tone(BUZZER_PIN, 1000, 300);
  delay(50);
}

bool isNeedToAlarm(int i, bool booked, bool confirmed) {
  if(!booked && occupied[i]) { return true; }
  if(booked && !confirmed && occupied[i]) { return true; }
  
  if(booked && confirmed && occupied[i]) { return false; }
  if(!occupied[i]) { return false; }
  else { return false; }
}

// =======================
// API: GET
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

  String response = http.getString();
  deserializeJson(doc, response);
  http.end();
  return true;
}

// =======================
// API: POST
// =======================
void sendToAPI() {
  if (WiFi.status() != WL_CONNECTED) return;

  StaticJsonDocument<512> doc;
  JsonArray arr = doc.createNestedArray("slots");

  for (int i = 0; i < AMOUNT_OF_SLOTS; i++) {
    JsonObject slot = arr.createNestedObject();
    slot["id_slot"] = i + 1; // TODO: Ini harus rada di di cek juga bisi seg fault
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

  pinMode(BUZZER_PIN, OUTPUT);

  for (int i = 0; i < 3; i++) {
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
  // 1. Read Ultrasonic
  for (int i = 0; i < AMOUNT_OF_SLOTS; i++) {
    float dist = measureDistance(SENSOR_PINS[i].trig, SENSOR_PINS[i].echo);
    occupied[i] = (dist < 10);
    Serial.print(occupied[i]);
    Serial.print(" ");
  }
  Serial.println();
  

  // 2. GET from API
  StaticJsonDocument<512> apiResponse;
  bool ok = getFromAPI(apiResponse);

  if (ok) {
    JsonArray slots = apiResponse["slots"].as<JsonArray>();
    JsonArray gates = apiResponse["gates"].as<JsonArray>();

    // --- Slot Warning Logic ---
    for(JsonObject slot : slots) {
      int id_slot = slot["id_slot"];
      bool booked = slot["booked"];
      bool confirmed = slot["confirmed"];

      int i = id_slot - 1; // TODO: Ini mesti di cek lagi id_slot valuenya dari brp (bising seg fault)
      alarmed[i] = isNeedToAlarm(i, booked, confirmed);
      if(alarmed[i]) { 
        alert(i) 
      }
    }

    // --- Gate Logic --- use openGate()
    for(JsonObject gate : gates) {
      int id_aktuator = gate["id_aktuator"];
      bool buka = gate["buka"];

      if(buka) {
        if(id_aktuator == 0) { openGate(enterGate); }
        else if (id_aktuator == 1) { openGate(exitGate);  }
        else { 
          Serial.print("Gate is not valid! Actuator ID: "); 
          Serial.println(id_aktuator);
        }
      }
    }
  }

  // 3. POST to API
  sendToAPI();

  delay(2000);
}
