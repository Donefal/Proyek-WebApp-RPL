/*
  22/11/2025
  Kode ini untuk melakukan test program dengan menggunakan board sementara ESP8266
  - Melakukan pengujian sensor
  - Melakukan pengujian komunikasi antara ESP dengan FastAPI via HTTP

  Untuk melakukan pengujian run FastAPI di direktori ../backend/test/fastAPI_esp8266.py
*/

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

// Ultrasonic Pins (USE D PINS from Wemos D1 Mini)
#define trigPin D2     // GPIO5
#define echoPin D1     // GPIO4

// WiFi Credentials
const char* ssid = "realme 8i";
const char* password = "avinavin";

// Server Endpoint
const char* serverUrl = "http://10.244.66.209:8000/api/update-slot-status";  // FastAPI endpoint

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Connected to: ");
    Serial.println(WiFi.SSID());
  } else {
    Serial.println("\nFailed to connect to WiFi");
  }
}

long measureDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000); // 30ms timeout
  long distance = duration * 0.034 / 2;
  return distance;
}

void sendToServer(const String& combinedStatus) {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;

    http.begin(client, serverUrl);  // <-- FIXED

    http.addHeader("Content-Type", "application/json");

    String payload = "{\"slot_id\":1,\"slot_number\":1,\"status\":\"" + combinedStatus + "\"}";
    int responseCode = http.POST(payload);

    Serial.print("HTTP Response Code: ");
    Serial.println(responseCode);

    if (responseCode > 0) {
      String response = http.getString();
      Serial.println("Response: " + response);
    } else {
      Serial.println("Failed to send POST request");
    }

    http.end();
  } else {
    Serial.println("WiFi not connected");
  }
}


void loop() {
  long distance = measureDistance();
  String status = (distance < 10) ? "occupied" : "available";
  String combinedStatus = String(distance) + "cm," + status;

  Serial.println(combinedStatus);
  sendToServer(combinedStatus);

  // Avoid watchdog reset
  for (int i = 0; i < 300; i++) {
    delay(100);  // 30 seconds total
  }
}

