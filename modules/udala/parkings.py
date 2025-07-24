import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import pandas as pd
import folium
import requests
from branca.element import Figure
from pyproj import Transformer

def obtener_parkings():
    url = "https://donostia.eus/info/ciudadano/camaras_trafico.nsf/getParkings.xsp"
    response = requests.get(url)
    data = response.json()
    parkings_data = []
    transformer = Transformer.from_crs("EPSG:25830", "EPSG:4326")

    for feature in data['features']:
        parking = feature['properties']
        coords_utm = feature['geometry']['coordinates']
        lat, lon = transformer.transform(coords_utm[0], coords_utm[1])
        parkings_data.append({
            "nombre": parking['nombre'],
            "lat": lat,
            "lon": lon,
            "libres": parking['libres'],
            "rotatorias": parking['plazasRotatorias'],
            "residentes": parking['plazasResidentes']
        })
    return pd.DataFrame(parkings_data)

def generar_mapa_parkings(df_parkings):
    if df_parkings.empty:
        return "<h3>No hay datos de parkings para mostrar.</h3>"

    fig = Figure(width=1000, height=800)
    m = folium.Map(location=[43.3187, -1.9805], zoom_start=14)
    folium.TileLayer('OpenStreetMap').add_to(m)
    fig.add_child(m)

    for _, row in df_parkings.iterrows():
        nombre = row["nombre"]
        libres = row["libres"]
        total = row["rotatorias"] + row["residentes"]
        popup_text = f"<b>{nombre}</b><br>Libres: {libres} / {total} plazas"
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color="blue", icon="car", prefix='fa')
        ).add_to(m)
    return m.get_root().render()

def layout():
    return html.Div([
        html.Div([
            html.H1("Mapa de Parkings Públicos en Donostia", style={
                "textAlign": "center",
                "color": "black",
                "fontSize": "2rem",
                "marginBottom": "15px",
            }),
            html.P([
            "Este mapa muestra los parkings públicos en Donostia. "
            "Cada marcador representa un aparcamiento y muestra en tiempo real el número de plazas disponibles. "
            "Puedes desplazarte por el mapa y hacer clic sobre los iconos para obtener más información detallada de cada parking. ",
            "Para más información, puede encontrar los datos en: ",
                html.A(
                    "donostia.eus - Transporte OTA",
                    href="https://www.donostia.eus/datosabiertos/catalogo/parkings_actual",
                    style={"color": "#007BFF", "textDecoration": "underline"}
                )],
                    style={
                        "textAlign": "center",
                        "color": "black",
                        "fontSize": "16px",
                        "fontFamily": "'Segoe UI', sans-serif",
                        "marginTop": "15px",
                        "marginBottom": "15px",
                    }
                ),
            ]),    
        dcc.Interval(
            id='interval-component-parkings',
            interval=5 * 60 * 1000,
            n_intervals=0
        ),
        dcc.Loading(
            id="loading-parkings",
            type="circle",
            fullscreen=False,
            children=html.Iframe(
                id='mapa-parkings',
                srcDoc="",
                width='100%',
                height='1000px',
                style={'border': 'none'}
            )
        )
    ])

def register_callbacks(app):
    @app.callback(
        Output('mapa-parkings', 'srcDoc'),
        Input('interval-component-parkings', 'n_intervals')
    )
    def update_map(n):
        df_parkings = obtener_parkings()
        return generar_mapa_parkings(df_parkings)
