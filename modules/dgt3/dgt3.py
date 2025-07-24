import dash
from dash import html, dcc, Input, Output, State
import datetime
import paramiko
import tempfile
import json
import pandas as pd
import folium
from branca.element import Figure
from dash.exceptions import PreventUpdate

REMOTE_HOST = "82.116.171.111"
REMOTE_PATH = "/received_data"

def download_json_file(date_str, username, password):
    filename = f"received_messages_{date_str}.json"
    full_path = f"{REMOTE_PATH}/{filename}"

    transport = paramiko.Transport((REMOTE_HOST, 22))
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    with sftp.open(full_path, 'r') as remote_file:
        content = remote_file.read()
    content_str = content.decode('utf-8')

    sftp.close()
    transport.close()

    # Guardar contenido en archivo temporal
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    with open(temp.name, 'w', encoding='utf-8') as f:
        f.write(content_str)

    return temp.name, filename

def cargar_datos_json_desde_sftp(date_str, username, password):
    filename = f"received_messages_{date_str}.json"
    full_path = f"{REMOTE_PATH}/{filename}"

    transport = paramiko.Transport((REMOTE_HOST, 22))
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    datos = []
    with sftp.open(full_path, 'r') as remote_file:
        for linea in remote_file:
            linea = linea.strip()
            if linea:
                datos.append(json.loads(linea))

    sftp.close()
    transport.close()

    return datos

def generar_mapa(datos):
    if not datos:
        m = folium.Map(location=[40.4, -3.75], zoom_start=6)
        return m.get_root().render()

    df = pd.DataFrame(datos)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by="timestamp")

    fig = Figure(width=1000, height=800)
    m = folium.Map(location=[40.4, -3.75], zoom_start=7, control_scale=True)
    fig.add_child(m)

    for action_id, grupo in df.groupby("actionId"):
        puntos = list(zip(grupo["latStart"], grupo["lonStart"]))
        folium.PolyLine(
            locations=puntos,
            color="blue",
            weight=4,
            opacity=0.7,
            popup=f"Ciclista: {action_id[:6]}..."
        ).add_to(m)

        folium.CircleMarker(
            location=puntos[0],
            radius=5,
            color="green",
            fill=True,
            tooltip="Inicio"
        ).add_to(m)

        folium.CircleMarker(
            location=puntos[-1],
            radius=5,
            color="red",
            fill=True,
            tooltip="Fin"
        ).add_to(m)

    return m.get_root().render()

layout = html.Div([
    html.Div([
        html.H1("Descarga de datos de ciclistas en vía pública", style={
            "textAlign": "center",
            "color": "black",
            "fontSize": "2rem",
            "marginBottom": "1px"
        }),
        html.P("Este módulo permite descargar un archivo JSON por fecha seleccionada de ciclistas en la vía pública y ver el mapa de los trayectos que han realizado los ciclistas en el mismo día.", style={
            "textAlign": "center",
            "fontSize": "16px"
        })
    ], style={"padding": "5px", "borderBottom": "1px solid #ddd"}),

    html.Div([
        html.Div([
            html.Label("Usuario:", style={"marginRight": "10px"}),
            dcc.Input(id='sftp-usuario', type='text', value='', placeholder='Introduce el usuario'),

            html.Label("Contraseña:", style={"marginLeft": "20px", "marginRight": "10px"}),
            dcc.Input(id='sftp-contrasena', type='password', value='', placeholder='Introduce la contraseña'),
        ], style={"textAlign": "center", "marginBottom": "20px"}),

        html.Div([
            html.Label("Selecciona la fecha:", style={"fontWeight": "bold", "marginRight": "10px"}),
            dcc.DatePickerSingle(
                id='fecha-sftp',
                display_format='YYYY-MM-DD',
                date=datetime.date.today(),
                style={
                    "border": "1px solid #ccc",
                    "borderRadius": "6px",
                    "padding": "8px",
                    "boxShadow": "0 1px 4px rgba(0,0,0,0.1)",
                    "fontSize": "14px"
                }
            )
        ], style={"marginBottom": "20px", "textAlign": "center"}),

        html.Div([
            html.Button("Ver mapa ciclistas", id="btn-ver-mapa", n_clicks=0, style={
                "backgroundColor": "blue",
                "color": "white",
                "border": "none",
                "borderRadius": "6px",
                "padding": "5px 10px",
                "fontSize": "14px",
                "cursor": "pointer",
                "boxShadow": "0 2px 6px rgba(0, 0, 0, 0.15)"
            }),
            html.Button("Descargar JSON", id="btn-descargar-sftp", n_clicks=0, style={
                "backgroundColor": "green",
                "color": "white",
                "border": "none",
                "borderRadius": "6px",
                "padding": "5px 10px",
                "fontSize": "14px",
                "cursor": "pointer",
                "boxShadow": "0 2px 6px rgba(0, 0, 0, 0.15)"
            }),
        ], style={"textAlign": "center", "marginBottom": "20px"}),

        dcc.Download(id="descarga-json-sftp")
    ], style={"padding": "20px", "maxWidth": "900px", "margin": "0 auto"}),

    html.Div(id="contenedor-mapa", style={"width": "100%", "height": "800px", "maxWidth": "900px", "margin": "0 auto"})
])



def register_callbacks(app):
    @app.callback(
        Output("descarga-json-sftp", "data"),
        Input("btn-descargar-sftp", "n_clicks"),
        State("fecha-sftp", "date"),
        State("sftp-usuario", "value"),
        State("sftp-contrasena", "value"),
        prevent_initial_call=True
    )
    def descargar_json(n, fecha, usuario, contrasena):
        if not fecha or not usuario or not contrasena:
            raise PreventUpdate
        try:
            fecha_str = fecha  # YYYY-MM-DD
            temp_path, filename = download_json_file(fecha_str, usuario, contrasena)
            return dcc.send_file(temp_path, filename=filename)
        except Exception as e:
            return dcc.send_string(f"Error al descargar el archivo: {str(e)}", filename="error.txt")

    @app.callback(
        Output("contenedor-mapa", "children"),
        Input("btn-ver-mapa", "n_clicks"),
        State("fecha-sftp", "date"),
        State("sftp-usuario", "value"),
        State("sftp-contrasena", "value"),
        prevent_initial_call=True
    )
    def mostrar_mapa(n_clicks, fecha, usuario, contrasena):
        if n_clicks is None or n_clicks == 0:
            raise PreventUpdate
        if not fecha or not usuario or not contrasena:
            return html.Div("Por favor, rellena todos los campos para ver el mapa.", style={"color": "red", "textAlign": "center"})
        
        try:
            datos = cargar_datos_json_desde_sftp(fecha, usuario, contrasena)
            mapa_html = generar_mapa(datos)
            return html.Iframe(srcDoc=mapa_html, style={"width": "100%", "height": "800px", "border": "none"})
        except Exception as e:
            return html.Div(f"Error al cargar el mapa: {str(e)}", style={"color": "red", "textAlign": "center"})