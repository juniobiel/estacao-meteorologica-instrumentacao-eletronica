import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import plotly.graph_objs as go
import paho.mqtt.client as mqtt
import threading
import queue
import json

# Configurações MQTT
BROKER = "377271ae85c448099dc71d8bd61e92c6.s1.eu.hivemq.cloud"
PORT = 8883
TOPIC = "sensores/dados"
CLIENT_ID = "dash-dashboard"
USERNAME = "FabricioTheTuffest"
PASSWORD = "Fabricio67"

# Fila para dados MQTT
dados_queue = queue.Queue()

# Dados coletados para o gráfico (últimos 10 valores)
dados_temperatura = []
dados_umidade = []
dados_luminosidade = []
timestamps = []

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Conectado com código {rc}")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        dados_queue.put(data)
        print(f"Recebido: {data}")
    except Exception as e:
        print(f"Erro ao processar mensagem MQTT: {e}")

def mqtt_loop():
    client = mqtt.Client(client_id=CLIENT_ID)
    client.username_pw_set(USERNAME, PASSWORD)
    client.tls_set()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_forever()

# Start MQTT in a background thread
threading.Thread(target=mqtt_loop, daemon=True).start()

# Inicializa app Dash
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Dashboard de Sensores - Dados em Tempo Real"),
    dcc.Graph(id='live-graph'),
    dcc.Interval(
        id='interval-component',
        interval=1*1000,  # em ms (1 segundo)
        n_intervals=0
    )
])

@app.callback(Output('live-graph', 'figure'),
              Input('interval-component', 'n_intervals'))
def update_graph_live(n):
    # Pega todos dados da fila
    while not dados_queue.empty():
        data = dados_queue.get()
        from datetime import datetime
        timestamps.append(datetime.now())
        dados_temperatura.append(data.get('temperatura', 0))
        dados_umidade.append(data.get('umidade', 0))
        dados_luminosidade.append(data.get('luminosidade', 0))

    # Mantém somente os últimos 10 pontos
    max_len = 10
    if len(timestamps) > max_len:
        timestamps[:] = timestamps[-max_len:]
        dados_temperatura[:] = dados_temperatura[-max_len:]
        dados_umidade[:] = dados_umidade[-max_len:]
        dados_luminosidade[:] = dados_luminosidade[-max_len:]

    # Monta gráfico com três linhas
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=timestamps,
        y=dados_temperatura,
        mode='lines+markers',
        name='Temperatura (°C)'
    ))

    fig.add_trace(go.Scatter(
        x=timestamps,
        y=dados_umidade,
        mode='lines+markers',
        name='Umidade (%)'
    ))

    fig.add_trace(go.Scatter(
        x=timestamps,
        y=dados_luminosidade,
        mode='lines+markers',
        name='Luminosidade (lux)'
    ))

    fig.update_layout(
        xaxis_title='Tempo',
        yaxis_title='Valores',
        template='plotly_dark',
        height=600
    )
    return fig

if __name__ == '__main__':
    app.run(debug=True)  # Mudança aqui! Substituímos run_server() por run()
