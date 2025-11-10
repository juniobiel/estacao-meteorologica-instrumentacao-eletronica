#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <DHTesp.h>
#include <BH1750.h>
#include <Adafruit_BMP280.h>
#include <AS5600.h>
#include <ArduinoJson.h>

// ==== CREDENCIAIS Wi-Fi ====
const char* WIFI_SSID = "Redmi Note 13";
const char* WIFI_PASS = "murilo123";

// ==== MQTT (HiveMQ Cloud) ====
const char* MQTT_BROKER = "377271ae85c448099dc71d8bd61e92c6.s1.eu.hivemq.cloud";
const int   MQTT_PORT   = 8883;
const char* MQTT_USER   = "FabricioTheTuffest";
const char* MQTT_PASS   = "Fabricio67";
const char* MQTT_TOPIC  = "sensores/dados";
const char* CLIENT_ID   = "esp32-estacao";

// ==== PINOS ====
#define DHTPIN 32
#define WIND_SENSOR_PIN 25
#define SDA_PIN 21
#define SCL_PIN 22

// ==== OBJETOS ====
DHTesp dht;
BH1750 lightMeter;
Adafruit_BMP280 bmp;
AS5600 encoder;
WiFiClientSecure secureClient;
PubSubClient mqttClient(secureClient);

// ==== VARIÁVEIS ====
float lastTempAvgVal = NAN;
float lastHumidityVal = NAN;
float lastLuxAvgVal = NAN;
float lastPressureVal = NAN;
float lastWindSpeed = NAN;
float lastAngle = NAN;
String lastDirectionStr = "";

// ==== INTERVALOS ====
const unsigned long LUX_INTERVAL = 30000;
const unsigned long LUX_AVG_INTERVAL = 180000;
const unsigned long PRESSURE_INTERVAL = 600000;
const unsigned long TEMP_INTERVAL = 30000;
const unsigned long TEMP_AVG_INTERVAL = 180000;
const unsigned long HUMIDITY_INTERVAL = 300000;
const unsigned long WIND_CALC_INTERVAL = 30000;
const unsigned long WIND_SEND_INTERVAL = 30000;
const unsigned long DIRECTION_INTERVAL = 300000;

unsigned long lastLux = 0;
unsigned long lastLuxAvg = 0;
unsigned long lastPressure = 0;
unsigned long lastTemp = 0;
unsigned long lastTempAvg = 0;
unsigned long lastHumidity = 0;
unsigned long lastWindCalc = 0;
unsigned long lastWindSend = 0;
unsigned long lastDirection = 0;

// ==== ANEMÔMETRO ====
volatile unsigned long pulseCount = 0;
const int HOLES = 10;
const float DIAMETER = 0.03;
float k = 1.0;

void IRAM_ATTR countPulse() { pulseCount++; }

float calcWindSpeed() {
  noInterrupts();
  unsigned long pulses = pulseCount;
  pulseCount = 0;
  interrupts();
  float rps = (float)pulses / HOLES;
  float circ = 3.1416 * DIAMETER;
  return k * rps * circ;
}

float weightedAverage(float *arr, int size) {
  if (size == 0) return 0;
  float ws = 0, tw = 0;
  for (int i = 0; i < size; i++) {
    float w = i + 1;
    ws += arr[i] * w;
    tw += w;
  }
  return ws / tw;
}

String direcaoCardeal(float angulo) {
  if (angulo >= 337.5 || angulo < 22.5)  return "N";
  else if (angulo < 67.5)  return "NO";
  else if (angulo < 112.5) return "O";
  else if (angulo < 157.5) return "SO";
  else if (angulo < 202.5) return "S";
  else if (angulo < 247.5) return "SE";
  else if (angulo < 292.5) return "L";
  else if (angulo < 337.5) return "NE";
  return "Indefinido";
}

// ==== MQTT / Wi-Fi ====
void connectWiFi() {
  Serial.print("Conectando Wi-Fi...");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\n✅ Wi-Fi conectado!");
}

void connectMQTT() {
  secureClient.setInsecure();
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  while (!mqttClient.connected()) {
    Serial.print("Conectando MQTT...");
    if (mqttClient.connect(CLIENT_ID, MQTT_USER, MQTT_PASS)) {
      Serial.println("✅ Conectado ao HiveMQ Cloud!");
    } else {
      Serial.print("❌ Falha MQTT: ");
      Serial.println(mqttClient.state());
      delay(5000);
    }
  }
}

void sendToMQTT(const char* tipo, float valor, const char* unidade, const char* extra = "") {
  StaticJsonDocument<256> doc;
  doc["sensor"] = tipo;
  doc["valor"] = valor;
  doc["unidade"] = unidade;
  if (extra[0] != '\0') doc["extra"] = extra;

  char payload[256];
  serializeJson(doc, payload);

  if (mqttClient.publish(MQTT_TOPIC, payload)) {
    Serial.printf("📤 [%s] Publicado no HiveMQ: %s\n", tipo, payload);
  } else {
    Serial.println("❌ Erro ao publicar MQTT!");
  }
}

// ==== SETUP ====
void setup() {
  Serial.begin(115200);
  Wire.begin(SDA_PIN, SCL_PIN);
  connectWiFi();
  connectMQTT();

  dht.setup(DHTPIN, DHTesp::DHT11);
  lightMeter.begin();
  bmp.begin(0x76);
  pinMode(WIND_SENSOR_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(WIND_SENSOR_PIN), countPulse, FALLING);

  Serial.println("=== Estação Meteorológica com Envio Automático (HiveMQ) ===");
}

// ==== LOOP ====
void loop() {
  if (!mqttClient.connected()) connectMQTT();
  mqttClient.loop();

  unsigned long now = millis();

  // === LUMINOSIDADE ===
  static float luxValues[6]; static int luxIndex = 0;
  if (now - lastLux >= LUX_INTERVAL) {
    lastLux = now;
    luxValues[luxIndex++ % 6] = lightMeter.readLightLevel();
  }
  if (now - lastLuxAvg >= LUX_AVG_INTERVAL) {
    lastLuxAvg = now;
    float luxAvg = weightedAverage(luxValues, 6);
    if (isnan(lastLuxAvgVal)) {
      Serial.printf("[BH1750] Primeira leitura: %.2f lux\n", luxAvg);
      lastLuxAvgVal = luxAvg;
      sendToMQTT("Luminosidade", luxAvg, "lux");
    } else if (abs(luxAvg - lastLuxAvgVal) > 50) {
      Serial.printf("[BH1750] Variação detectada: %.2f lux\n", luxAvg);
      lastLuxAvgVal = luxAvg;
      sendToMQTT("Luminosidade", luxAvg, "lux");
    }
  }

  // === PRESSÃO ===
  if (now - lastPressure >= PRESSURE_INTERVAL) {
    lastPressure = now;
    float p = bmp.readPressure() / 100.0;
    if (isnan(lastPressureVal)) {
      Serial.printf("[BMP280] Primeira leitura pressão: %.2f hPa\n", p);
      lastPressureVal = p;
      sendToMQTT("Pressao", p, "hPa");
    } else if (abs(p - lastPressureVal) > 30 && p >= 800 && p <= 1060) {
      Serial.printf("[BMP280] Variação detectada pressao: %.2f hPa\n", p);
      lastPressureVal = p;
      sendToMQTT("Pressao", p, "hPa");
    }
  }

  // === TEMPERATURA ===
  static float tempValues[6]; static int tempIndex = 0;
  if (now - lastTemp >= TEMP_INTERVAL) {
    lastTemp = now;
    tempValues[tempIndex++ % 6] = bmp.readTemperature();
  }
  if (now - lastTempAvg >= TEMP_AVG_INTERVAL) {
    lastTempAvg = now;
    float avgT = weightedAverage(tempValues, 6);
    if (isnan(lastTempAvgVal)) {
      Serial.printf("[BMP280] Primeira leitura temperatura: %.2f°C\n", avgT);
      lastTempAvgVal = avgT;
      sendToMQTT("Temperatura", avgT, "°C");
    } else if (abs(avgT - lastTempAvgVal) > 1.0) {
      Serial.printf("[BMP280] Variação detectada temperatura: %.2f°C\n", avgT);
      lastTempAvgVal = avgT;
      sendToMQTT("Temperatura", avgT, "°C");
    }
  }

  // === UMIDADE ===
  if (now - lastHumidity >= HUMIDITY_INTERVAL) {
    lastHumidity = now;
    float h = dht.getHumidity();
    if (!isnan(h) && h >= 0 && h <= 90) {
      h = round(h / 5.0) * 5;
      if (isnan(lastHumidityVal)) {
        Serial.printf("[DHTesp] Primeira leitura: %.0f%%\n", h);
        lastHumidityVal = h;
        sendToMQTT("Umidade", h, "%");
      } else if (abs(h - lastHumidityVal) >= 5) {
        Serial.printf("[DHTesp] Variação detectada: %.0f%%\n", h);
        lastHumidityVal = h;
        sendToMQTT("Umidade", h, "%");
      }
    }
  }

  // === VELOCIDADE DO VENTO ===
  if (now - lastWindCalc >= WIND_CALC_INTERVAL) {
    lastWindCalc = now;
    float windSpeed = calcWindSpeed();
    if (isnan(lastWindSpeed)) {
      Serial.printf("[LM393] Primeira leitura velocidade vento: %.2f m/s\n", windSpeed);
      lastWindSpeed = windSpeed;
      sendToMQTT("Vento", windSpeed, "m/s");
    } else if (abs(windSpeed - lastWindSpeed) > 0.05) {
      Serial.printf("[LM393] Variação detectada velocidade: %.2f m/s\n", windSpeed);
      lastWindSpeed = windSpeed;
      sendToMQTT("Vento", windSpeed, "m/s");
    }
  }

  // === DIREÇÃO DO VENTO ===
  if (now - lastDirection >= DIRECTION_INTERVAL) {
    lastDirection = now;
    if (encoder.isConnected()) {
      uint16_t raw = encoder.readAngle();
      float angulo = (raw * 360.0) / 4096.0;
      String direcao = direcaoCardeal(angulo);
      if (isnan(lastAngle)) {
        Serial.printf("[AS5600] Primeira leitura: %.2f° -> %s\n", angulo, direcao.c_str());
        lastAngle = angulo;
        lastDirectionStr = direcao;
        sendToMQTT("Direcao", angulo, "°", direcao.c_str());
      } else if (abs(angulo - lastAngle) > 10.0) {
        Serial.printf("[AS5600] Variação detectada: %.2f° -> %s\n", angulo, direcao.c_str());
        lastAngle = angulo;
        lastDirectionStr = direcao;
        sendToMQTT("Direcao", angulo, "°", direcao.c_str());
      }
    }
  }
}
