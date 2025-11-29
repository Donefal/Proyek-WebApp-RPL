/*
  TODO: ROMBAK
  1. Ultrasonic diubah menjadi 2 aja
  2. Implementasi send_instruction_to_esp32_test() dari hardware.py
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
// TODO: Endpoint disesuaikan dengan hardware.py
// =======================
String GET_URL = "http://10.34.222.209:8000/hw/get";
String POST_URL = "http://10.34.222.209:8000/hw/update";

// =======================
// Ultrasonic Pins
// =======================
struct Ultrasonic {
  int trig;
  int echo;
};

Ultrasonic sensors[3] = {
  {18, 19},   // slot 1
  {16, 17},  // slot 2
  {25, 26}   // slot 3 (35 is input-only → perfect)
};

bool occupied[3] = {false, false, false};
bool calculated[3] = {false, false, false};

// =======================
// Servos
// =======================
Servo enterGate;
Servo exitGate;

int ENTER_GATE_PIN = 13;
int EXIT_GATE_PIN = 14;

// =======================
// Buzzer
// =======================
int BUZZER_PIN = 27;

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

// =======================
// API: GET
// TODO: Data type sesuaiin dengan send_instruction_esp32() di hardware.py
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
// TODO: Data type sesuaiin dengan update_from_esp32() di hardware.py
// =======================
void sendToAPI() {
  if (WiFi.status() != WL_CONNECTED) return;

  StaticJsonDocument<256> doc;
  JsonArray arr = doc.createNestedArray("slots");

  for (int i = 0; i < 3; i++) {
    JsonObject slot = arr.createNestedObject();
    slot["no"] = i + 1;
    slot["occupied"] = occupied[i];
    slot["calculated"] = calculated[i];
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
    pinMode(sensors[i].trig, OUTPUT);
    pinMode(sensors[i].echo, INPUT);
  }

  enterGate.attach(ENTER_GATE_PIN);
  exitGate.attach(EXIT_GATE_PIN);

  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print("x");
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
  for (int i = 0; i < 3; i++) {
    float dist = measureDistance(sensors[i].trig, sensors[i].echo);
    occupied[i] = (dist < 10);
    Serial.print(occupied[i]);
    Serial.println();
  }
  

  // 2. GET from API
  StaticJsonDocument<512> apiResponse;
  bool ok = getFromAPI(apiResponse);

  if (ok) {
    JsonArray slots = apiResponse["slots"];
    JsonObject gate = apiResponse["gate"];

    // --- Slot Warning Logic ---
    for (int i = 0; i < 3; i++) {
      bool booked = slots[i]["booked"];
      bool confirmed = slots[i]["confirmed"];
      bool calc = slots[i]["calculated"];

      if (!calc) {
        if (occupied[i] && !confirmed) alert(i);
        if (occupied[i] && !booked) alert(i);
        if (occupied[i] && booked && confirmed) calculated[i] = true;
      }
    }

    // --- Gate Logic ---
    if (gate["enterShouldOpen"]) openGate(enterGate);
    if (gate["exitShouldOpen"]) openGate(exitGate);
  }

  // 3. POST to API
  sendToAPI();

  delay(2000);
}
