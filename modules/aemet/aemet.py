import os
import dash
from dash import dcc, html, Input, Output
import pandas as pd
import folium
import requests
import json
import time
from branca.element import Figure

ruta_ubicacion = os.path.join(os.path.dirname(__file__), "../../data/aemet/ubicacion.txt")


API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJtenVhem9sYWFyckBhbHVtbmkudW5hdi5lcyIsImp0aSI6IjdjNzQwYWFiLTMzYjktNDlkMy1iYTZkLWIyYTJmMTBmZjkxYyIsImlzcyI6IkFFTUVUIiwiaWF0IjoxNzQ4OTQ2NDE5LCJ1c2VySWQiOiI3Yzc0MGFhYi0zM2I5LTQ5ZDMtYmE2ZC1iMmEyZjEwZmY5MWMiLCJyb2xlIjoiIn0.KT5c-hwta3Y7yC1E-147KbS-uKywZGcyV-iN6zvRu2M"

def sexagesimal_a_decimal(coord, tipo):
    try:
        if tipo == "lat":
            if len(coord) != 7:
                raise ValueError(f"Formato de latitud inesperado (longitud {len(coord)}): '{coord}'")
            grados = int(coord[:2])
            minutos = int(coord[2:4])
            segundos = int(coord[4:6])
            direccion = coord[6]
        else:  # tipo == "lon"
            if len(coord) == 7:
                grados = int(coord[:2])
                minutos = int(coord[2:4])
                segundos = int(coord[4:6])
                direccion = coord[6]
            elif len(coord) == 8:
                grados = int(coord[:3])
                minutos = int(coord[3:5])
                segundos = int(coord[5:7])
                direccion = coord[7]
            else:
                raise ValueError(f"Formato de longitud desconocido (longitud {len(coord)}): '{coord}'")
        
        decimal = grados + minutos / 60 + segundos / 3600
        if direccion in ['S', 'W']:
            decimal *= -1
        return decimal
    except (ValueError, IndexError) as e:
        print(f"Error al convertir coordenada '{coord}' de tipo '{tipo}': {e}")
        return None

def obtener_datos_estaciones():
    print("\n--- Iniciando obtención de datos de estaciones ---")
    try:
        with open(os.path.abspath(ruta_ubicacion), encoding="iso-8859-1") as f:
            estaciones = json.load(f)
        print("Archivo 'ubicacion.txt' cargado exitosamente.")
    except Exception as e:
        print(f"ERROR al cargar 'ubicacion.txt': {e}")
        return pd.DataFrame()

    gipuzkoa_estaciones = [e for e in estaciones if e.get("provincia", "").upper() == "GIPUZKOA"]
    datos = []

    if not gipuzkoa_estaciones:
        print("No se encontraron estaciones para GIPUZKOA.")
        return pd.DataFrame()
    else:
        print(f"Encontradas {len(gipuzkoa_estaciones)} estaciones en GIPUZKOA.")

    url_api_todas = "https://opendata.aemet.es/opendata/api/observacion/convencional/todas"
    headers = {"api_key": API_KEY}
    
    try:
        response_url = requests.get(url_api_todas, headers=headers, timeout=15) 
        response_url.raise_for_status()
        r_url = response_url.json()
        datos_obs_url = r_url.get("datos")
        if not datos_obs_url:
            print("No se obtuvo URL de datos de la API.")
            return pd.DataFrame()
        time.sleep(0.5)
        response_obs = requests.get(datos_obs_url, timeout=30)
        response_obs.raise_for_status()
        all_observations = response_obs.json()
    except Exception as e:
        print(f"Error al obtener datos de AEMET: {e}")
        return pd.DataFrame()

    for est in gipuzkoa_estaciones:
        indicativo = est.get("indicativo")
        nombre = est.get("nombre", "Desconocido")
        lat_sex = est.get("latitud")
        lon_sex = est.get("longitud")

        if not all([indicativo, lat_sex, lon_sex]):
            print(f"Datos incompletos para {nombre}, se salta.")
            continue
        
        lat = sexagesimal_a_decimal(lat_sex, "lat")
        lon = sexagesimal_a_decimal(lon_sex, "lon")
        if lat is None or lon is None:
            print(f"Error en coordenadas de {nombre}, se salta.")
            continue
        
        estacion_data = [obs for obs in all_observations if obs.get("idema") == indicativo]
        if not estacion_data:
            print(f"No hay datos para {nombre}.")
            continue
        
        ultima_obs = estacion_data[-1]

        datos.append({
            "nombre": nombre,
            "altitud": est.get("altitud", "nd"),
            "lat": lat,
            "lon": lon,
            "fecha": ultima_obs.get("fint", "nd"),
            "t": ultima_obs.get("ta", "nd"),
            "v": ultima_obs.get("vv", "nd"),
            "r": ultima_obs.get("vmax", "nd"),
            "prec": ultima_obs.get("prec", "nd"),
            "pres": ultima_obs.get("pres", "nd"),
            "hum": ultima_obs.get("hr", "nd"),
        })
        time.sleep(0.1)

    print("\n--- Fin de obtención de datos ---")
    return pd.DataFrame(datos)

def generar_mapa():
    df = obtener_datos_estaciones()
    fig = Figure(width=1000, height=800)
    m = folium.Map(location=[43.3183, -1.9812], zoom_start=9)
    fig.add_child(m)

    if df.empty:
        print("No hay datos para mostrar en el mapa.")
        folium.Marker(
            location=[43.2, -2.2],
            popup="No se pudieron cargar los datos de las estaciones.",
            icon=folium.Icon(color="blue", icon="info", prefix='fa')
        ).add_to(m)
    else:
        for _, row in df.iterrows():
            popup = f"""
            <b>{row['nombre']}</b><br>
            Altitud: {row['altitud']} m<br>
            Fecha: {row['fecha']}<br><br>
            🌡 Temp: {row['t']} °C<br>
            💨 Viento: {row['v']} km/h<br>
            🌬 Racha: {row['r']} km/h<br>
            🌧 Precip.: {row['prec']} mm<br>
            📈 Presión: {row['pres']} hPa<br>
            💧 Humedad: {row['hum']} %
            """
            folium.Marker(
                location=[row["lat"], row["lon"]],
                tooltip=row["nombre"],
                popup=folium.Popup(popup, max_width=250),
                icon=folium.Icon(color="red", icon="cloud", prefix='fa')
            ).add_to(m)
    return m.get_root().render()


def layout():
    return html.Div([
        html.Div([
              html.H1("Mapa de Estaciones Metereológicas en Gipuzkoa", style={
                "textAlign": "center",
                "color": "black",
                "fontSize": "2rem",
                "marginBottom": "15px",
            }),
        html.P([
        "Este mapa muestra las estaciones meteorológicas propiedad de AEMET disponibles en Gipuzkoa, "
        "con datos en tiempo real sobre temperatura, viento, precipitación y más. "
        "Los marcadores indican la ubicación exacta de cada estación. "
        "Puedes hacer zoom y desplazarte para explorar las distintas localidades. "
        "Haz clic en un marcador para ver los datos detallados de la estación. ",
        "Para más información, puede encontrar los datos en: ",
                html.A(
                    "opendata.aemet.es",
                    href="https://opendata.aemet.es/centrodedescargas/productosAEMET?",
                    target="_blank",
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

        dcc.Loading(
            id="loading",
            type="circle",
            fullscreen=False,
            children=[
                html.Iframe(
                    id='mapa',
                    srcDoc=generar_mapa(),
                    width='100%',
                    height='1000px',
                    style={'border': 'none'}
                ),
                dcc.Interval(
                    id='interval-component',
                    interval=300 * 1000,
                    n_intervals=0
                )
            ]
        )
    ], style={"margin": "0", "padding": "0", "position": "relative"})


def registrar_callbacks(app):
    @app.callback(
        Output('mapa', 'srcDoc'),
        Input('interval-component', 'n_intervals')
    )
    def update_map_live(n_intervals):
        print(f"\n--- Actualizando mapa (intervalo: {n_intervals}) ---")
        return generar_mapa()
