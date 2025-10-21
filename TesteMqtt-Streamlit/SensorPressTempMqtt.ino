#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BMP280.h>

// === CONFIGURAÇÃO WI-FI ===
const char* ssid = "SEU_WIFI";
const char* password = "SUA_SENHA";

// === CONFIGURAÇÃO MQTT ===
const char* mqtt_server = "192.168.0.100";  // IP local do PC com Mosquitto
const int mqtt_port = 1883;
const char* mqtt_user = "";    // se não usar autenticação, deixe vazio
const char* mqtt_password = "";

WiFiClient espClient;
PubSubClient client(espClient);
Adafruit_BMP280 bmp;  // sensor BMP280 (via I2C)

unsigned long lastTime = 0;
const long interval = 1000; // intervalo de leitura (ms)

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);  // SDA, SCL — pinos padrão do ESP32

  Serial.println("Iniciando sensor BMP280...");
  if (!bmp.begin(0x76)) {  // Endereço I2C: 0x76 ou 0x77
    Serial.println("❌ Sensor BMP280 não encontrado!");
    while (1);
  }
  Serial.println("✅ Sensor BMP280 detectado!");

  WiFi.begin(ssid, password);
  Serial.print("Conectando ao Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n📶 Conectado ao Wi-Fi com IP: " + WiFi.localIP().toString());

  client.setServer(mqtt_server, mqtt_port);
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("🔌 Conectando ao broker MQTT... ");
    if (client.connect("ESP32_BMP280", mqtt_user, mqtt_password)) {
      Serial.println("✅ Conectado!");
      // client.subscribe("topico/teste"); // se quiser assinar algo
    } else {
      Serial.print("❌ falha, rc=");
      Serial.print(client.state());
      Serial.println(" — tentando novamente em 5s");
      delay(5000);
    }
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long currentTime = millis();
  if (currentTime - lastTime >= interval) {
    lastTime = currentTime;

    float temperatura = bmp.readTemperature();   // em °C
    float pressao = bmp.readPressure() / 100.0F; // em hPa

    // Imprime no monitor serial
    Serial.print("🌡️ Temperatura: ");
    Serial.print(temperatura);
    Serial.print(" °C\t🧭 Pressão: ");
    Serial.print(pressao);
    Serial.println(" hPa");

    // Monta JSON
    String payload = "{\"temperatura\": " + String(temperatura, 2) + 
                     ", \"pressao\": " + String(pressao, 2) + "}";

    // Envia para o broker
    client.publish("sensor/bmp280", payload.c_str());
  }
}

*/

📌 Tópico MQTT usado:
sensor/bmp280


Você pode se inscrever com o Mosquitto assim:

mosquitto_sub -h localhost -t "sensor/bmp280"


E verá algo como:

{"temperatura": 24.57, "pressao": 1013.21}

2. Testar se o broker está rodando

Abra um terminal e execute:

mosquitto_sub -h localhost -t "teste/topic"


Esse comando “escuta” as mensagens no tópico teste/topic.

Em outro terminal, envie uma mensagem teste:

mosquitto_pub -h localhost -t "teste/topic" -m "Olá MQTT"


Se você vir a mensagem aparecer no terminal que está “ouvindo”, o broker está funcionando!

/*