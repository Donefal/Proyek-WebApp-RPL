#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// =======================
// WiFi Credentials
// =======================
const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASSWORD";

// =======================
// API Endpoints
// =======================
String GET_URL = "http://127.0.0.1:8000/api/get";
String POST_URL = "http://127.0.0.1:8000/api/update";

// =======================
// Ultrasonic Pins
// =======================
struct Ultrasonic {
  int trig;
  int echo;
};

Ultrasonic sensors[3] = {
  {4, 5},     // slot 1
  {18, 19},   // slot 2
  {21, 22}    // slot 3
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

  if (duration == 0) return 999;  
  return distance;
}

void alert(int slot) {
  tone(BUZZER_PIN, 1000, 300);
  delay(50);
}

// =======================
// API: GET
// =======================
bool getFromAPI(JsonDocument &doc) {
  if (WiFi.status() != WL_CONNECTED) return false;

  HTTPClient http;
  http.begin(GET_URL);

  int code = http.GET();
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
    Serial.print(".");
    delay(500);
  }

  Serial.println("\nConnected!");
}

// =======================
// LOOP
// =======================
void loop() {
  // 1. Read Ultrasonic
  for (int i = 0; i < 3; i++) {
    float dist = measureDistance(sensors[i].trig, sensors[i].echo);
    occupied[i] = (dist < 10);
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
