import paho.mqtt.client as mqtt
import json
import random
import time

BROKER = "377271ae85c448099dc71d8bd61e92c6.s1.eu.hivemq.cloud"
PORT = 8883
TOPIC = "sensores/dados"
CLIENT_ID = "simulador-python"
USERNAME = "FabricioTheTuffest"
PASSWORD = "Fabricio67"

def generate_sensor_data():
    return {
        "temperatura": round(random.uniform(20.0, 30.0), 2),
        "umidade": round(random.uniform(30.0, 70.0), 2),
        "luminosidade": round(random.uniform(100, 1000), 2)
    }

client = mqtt.Client(client_id=CLIENT_ID)
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()
client.connect(BROKER, PORT, 60)

while True:
    data = generate_sensor_data()
    payload = json.dumps(data)
    client.publish(TOPIC, payload)
    print(f"Enviado: {payload}")
    time.sleep(5)
