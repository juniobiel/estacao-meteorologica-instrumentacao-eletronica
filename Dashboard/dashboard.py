import dash
from dash import dcc, html, Output, Input
import plotly.graph_objs as go
import paho.mqtt.client as mqtt
import threading
import queue
import json
from datetime import datetime
import time

# =============================
# CONFIGURAÇÕES MQTT
# =============================
BROKER = "377271ae85c448099dc71d8bd61e92c6.s1.eu.hivemq.cloud"
PORT = 8883
TOPIC = "sensores/dados"
CLIENT_ID = "dash-dashboard"
USERNAME = "FabricioTheTuffest"
PASSWORD = "Fabricio67"

# =============================
# FILA E DADOS
# =============================
dados_queue = queue.Queue()
MAX_PONTOS = 20

dados = {
    "tempo_temp": [], "temperatura": [],
    "tempo_umid": [], "umidade": [],
    "tempo_lux": [], "luminosidade": [],
    "tempo_pressao": [], "pressao": [],
    "tempo_vento": [], "vento": [],
    "direcao": []
}

stats = {
    "temp_max": None, "temp_min": None,
    "umid_max": None, "umid_min": None,
    "lux_max": None, "lux_min": None,
    "pressao_max": None, "pressao_min": None,
    "vento_max": None, "vento_min": None,
    "ultima_direcao": "—"
}

# =============================
# MQTT
# =============================
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[MQTT] Conectado!")
        client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        print(f"[MQTT] Recebido: {payload}")
        dados_queue.put(payload)
    except Exception as e:
        print(f"[MQTT] Erro: {e}")

def mqtt_thread():
    client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(USERNAME, PASSWORD)
    client.tls_set()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.loop_forever()

threading.Thread(target=mqtt_thread, daemon=True).start()
time.sleep(2)

# =============================
# DASH APP
# =============================
app = dash.Dash(__name__)
app.title = "Estação Meteorológica"

app.layout = html.Div([
    # === PAINEL SUPERIOR: 6 CARDS ===
    html.Div([
        # CARD TEMPERATURA
        html.Div([
            html.H2("Temperatura", style={'fontSize': 18, 'margin': '0 0 5px 0', 'color': '#ccc'}),
            html.H1(id='valor-temp', style={'fontSize': 48, 'margin': '0', 'color': '#fff'}),
            html.Div([
                html.Span(id='temp-max', style={'color': '#ff8c8c'}),
                html.Span(" | "),
                html.Span(id='temp-min', style={'color': '#8c8cff'})
            ], style={'fontSize': 14, 'color': '#aaa'})
        ], className='card'),

        # CARD UMIDADE
        html.Div([
            html.H2("Umidade", style={'fontSize': 18, 'margin': '0 0 5px 0', 'color': '#ccc'}),
            html.H1(id='valor-umid', style={'fontSize': 48, 'margin': '0', 'color': '#fff'}),
            html.Div([
                html.Span(id='umid-max', style={'color': '#8cff8c'}),
                html.Span(" | "),
                html.Span(id='umid-min', style={'color': '#8c8cff'})
            ], style={'fontSize': 14, 'color': '#aaa'})
        ], className='card'),

        # CARD LUMINOSIDADE
        html.Div([
            html.H2("Luminosidade", style={'fontSize': 18, 'margin': '0 0 5px 0', 'color': '#ccc'}),
            html.H1(id='valor-lux', style={'fontSize': 48, 'margin': '0', 'color': '#fff'}),
            html.Div([
                html.Span(id='lux-max', style={'color': '#ffeb8c'}),
                html.Span(" | "),
                html.Span(id='lux-min', style={'color': '#8c8cff'})
            ], style={'fontSize': 14, 'color': '#aaa'})
        ], className='card'),

        # CARD PRESSÃO
        html.Div([
            html.H2("Pressão", style={'fontSize': 18, 'margin': '0 0 5px 0', 'color': '#ccc'}),
            html.H1(id='valor-pressao', style={'fontSize': 48, 'margin': '0', 'color': '#fff'}),
            html.Div([
                html.Span(id='pressao-max', style={'color': '#d88cff'}),
                html.Span(" | "),
                html.Span(id='pressao-min', style={'color': '#8c8cff'})
            ], style={'fontSize': 14, 'color': '#aaa'})
        ], className='card'),

        # CARD VENTO
        html.Div([
            html.H2("Vel. Vento", style={'fontSize': 18, 'margin': '0 0 5px 0', 'color': '#ccc'}),
            html.H1(id='valor-vento', style={'fontSize': 48, 'margin': '0', 'color': '#fff'}),
            html.Div([
                html.Span(id='vento-max', style={'color': '#8cff8c'}),
                html.Span(" | "),
                html.Span(id='vento-min', style={'color': '#8c8cff'})
            ], style={'fontSize': 14, 'color': '#aaa'})
        ], className='card'),

        # CARD DIREÇÃO (SEPARADO!)
        html.Div([
            html.H2("Direção", style={'fontSize': 18, 'margin': '0 0 5px 0', 'color': '#ccc'}),
            html.H1(id='valor-direcao', style={'fontSize': 48, 'margin': '0', 'color': '#00ff88', 'fontWeight': 'bold'}),
        ], className='card'),
    ], style={
        'display': 'grid',
        'gridTemplateColumns': 'repeat(auto-fit, minmax(180px, 1fr))',
        'gap': '15px',
        'padding': '20px',
        'maxWidth': '1400px',
        'margin': '0 auto'
    }),

    # === GRÁFICOS ===
    html.Div([
        html.Div(dcc.Graph(id='graph-temp'), className='grafico'),
        html.Div(dcc.Graph(id='graph-umid'), className='grafico'),
        html.Div(dcc.Graph(id='graph-lux'), className='grafico'),
        html.Div(dcc.Graph(id='graph-pressao'), className='grafico'),
        html.Div(dcc.Graph(id='graph-vento'), className='grafico'),
    ], style={
        'display': 'grid',
        'gridTemplateColumns': 'repeat(auto-fit, minmax(400px, 1fr))',
        'gap': '20px',
        'padding': '20px',
        'maxWidth': '1400px',
        'margin': '0 auto'
    }),

    dcc.Interval(id='interval-update', interval=2000, n_intervals=0)
], style={'background': 'linear-gradient(to bottom, #87CEEB, #1e1e1e)', 'minHeight': '100vh', 'fontFamily': 'Arial'})

# === CSS ===
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}<title>{%title%}</title>{%favicon%}{%css%}
        <style>
            .card {
                background: rgba(255,255,255,0.1);
                padding: 18px;
                border-radius: 20px;
                text-align: center;
                backdrop-filter: blur(12px);
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                transition: 0.3s;
                border: 1px solid rgba(255,255,255,0.1);
            }
            .card:hover { transform: translateY(-5px); }
            .grafico { background: rgba(30,30,30,0.8); border-radius: 15px; padding: 10px; }
        </style>
    </head>
    <body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body>
</html>
'''

# =============================
# CALLBACK
# =============================
@app.callback(
    [Output('valor-temp', 'children'), Output('temp-max', 'children'), Output('temp-min', 'children'),
     Output('valor-umid', 'children'), Output('umid-max', 'children'), Output('umid-min', 'children'),
     Output('valor-lux', 'children'), Output('lux-max', 'children'), Output('lux-min', 'children'),
     Output('valor-pressao', 'children'), Output('pressao-max', 'children'), Output('pressao-min', 'children'),
     Output('valor-vento', 'children'), Output('vento-max', 'children'), Output('vento-min', 'children'),
     Output('valor-direcao', 'children'),
     Output('graph-temp', 'figure'), Output('graph-umid', 'figure'), Output('graph-lux', 'figure'),
     Output('graph-pressao', 'figure'), Output('graph-vento', 'figure')],
    Input('interval-update', 'n_intervals')
)
def update_all(n):
    try:
        direcao_forcada = stats["ultima_direcao"]

        while not dados_queue.empty():
            msg = dados_queue.get_nowait()
            sensor = str(msg.get("sensor", "")).strip()
            valor = msg.get("valor", 0)
            extra = str(msg.get("extra", "")).strip()
            tempo = datetime.now().strftime("%H:%M:%S")

            s = sensor.lower().replace("ã", "a").replace("ç", "c")
            s = s.replace(" ", "").replace("-", "").replace("_", "")

            def update_stat(key, v):
                if stats[f"{key}_max"] is None or v > stats[f"{key}_max"]:
                    stats[f"{key}_max"] = v
                if stats[f"{key}_min"] is None or v < stats[f"{key}_min"]:
                    stats[f"{key}_min"] = v

            if "temperatura" in s:
                v = float(valor)
                dados["temperatura"].append(v)
                dados["tempo_temp"].append(tempo)
                update_stat("temp", v)
            elif "umidade" in s:
                v = float(valor)
                dados["umidade"].append(v)
                dados["tempo_umid"].append(tempo)
                update_stat("umid", v)
            elif "luminos" in s or "lux" in s:
                v = float(valor)
                dados["luminosidade"].append(v)
                dados["tempo_lux"].append(tempo)
                update_stat("lux", v)
            elif "pressao" in s:
                v = float(valor)
                dados["pressao"].append(v)
                dados["tempo_pressao"].append(tempo)
                update_stat("pressao", v)
            elif "vento" in s and "dire" not in s:
                v = float(valor)
                dados["vento"].append(v)
                dados["tempo_vento"].append(tempo)
                update_stat("vento", v)
            elif "dire" in s:
                direcao = extra.upper() if extra else "—"
                dados["direcao"].append(direcao)
                stats["ultima_direcao"] = direcao
                direcao_forcada = f"{direcao} "  # FORÇA ATUALIZAÇÃO

        # === LIMITA PONTOS ===
        for k in ["temperatura", "umidade", "luminosidade", "pressao", "vento"]:
            tk = f"tempo_{k}"
            if len(dados[k]) > MAX_PONTOS:
                dados[k] = dados[k][-MAX_PONTOS:]
                dados[tk] = dados[tk][-MAX_PONTOS:]

        # === ÚLTIMOS VALORES ===
        def last(k):
            return dados[k][-1] if dados[k] else 0

        # === GRÁFICO ===
        def line_fig(title, y, label, color, tk):
            if not y:
                fig = go.Figure()
                fig.update_layout(title=title, template="plotly_dark", height=300)
                return fig
            return go.Figure(
                data=[go.Scatter(x=dados[tk], y=y, mode='lines+markers', line=dict(color=color, width=2))],
                layout=go.Layout(title=title, xaxis=dict(title="Tempo"), yaxis=dict(title=label), template="plotly_dark", height=300)
            )

        return (
            f"{last('temperatura'):.1f}",
            f"Máx: {stats['temp_max']:.1f}" if stats['temp_max'] is not None else "Máx: —",
            f"Mín: {stats['temp_min']:.1f}" if stats['temp_min'] is not None else "Mín: —",
            f"{last('umidade'):.0f}",
            f"Máx: {stats['umid_max']:.0f}" if stats['umid_max'] is not None else "Máx: —",
            f"Mín: {stats['umid_min']:.0f}" if stats['umid_min'] is not None else "Mín: —",
            f"{last('luminosidade'):.0f}",
            f"Máx: {stats['lux_max']:.0f}" if stats['lux_max'] is not None else "Máx: —",
            f"Mín: {stats['lux_min']:.0f}" if stats['lux_min'] is not None else "Mín: —",
            f"{last('pressao'):.1f}",
            f"Máx: {stats['pressao_max']:.1f}" if stats['pressao_max'] is not None else "Máx: —",
            f"Mín: {stats['pressao_min']:.1f}" if stats['pressao_min'] is not None else "Mín: —",
            f"{last('vento'):.1f}",
            f"Máx: {stats['vento_max']:.1f}" if stats['vento_max'] is not None else "Máx: —",
            f"Mín: {stats['vento_min']:.1f}" if stats['vento_min'] is not None else "Mín: —",
            direcao_forcada,
            line_fig("Temperatura", dados["temperatura"], "°C", "#FF5733", "tempo_temp"),
            line_fig("Umidade", dados["umidade"], "%", "#33C1FF", "tempo_umid"),
            line_fig("Luminosidade", dados["luminosidade"], "lux", "#FFD633", "tempo_lux"),
            line_fig("Pressão", dados["pressao"], "hPa", "#9B59B6", "tempo_pressao"),
            line_fig("Vento", dados["vento"], "m/s", "#33FF88", "tempo_vento")
        )
    except Exception as e:
        print(f"[ERRO]: {e}")
        return (
            "—", "Máx: —", "Mín: —",
            "—", "Máx: —", "Mín: —",
            "—", "Máx: —", "Mín: —",
            "—", "Máx: —", "Mín: —",
            "—", "Máx: —", "Mín: —",
            "— ",
            go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure()
        )

# =============================
# EXECUÇÃO
# =============================
if __name__ == "__main__":
    print("[DASH] Iniciando servidor...")
    app.run(debug=False, host='127.0.0.1', port=8050)