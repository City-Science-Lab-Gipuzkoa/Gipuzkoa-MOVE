import dash
from dash import dcc, html, Input, Output
import pandas as pd
import folium
from branca.element import Figure

EXCEL_PATH = "data/incidencias/camaras-trafico.xlsx"

def obtener_camaras_trafico():
    camaras_data = []
    try:
        df_excel = pd.read_excel(EXCEL_PATH)

        if df_excel.empty:
            return pd.DataFrame()

        required_columns = ["LATWGS84", "LONWGS84", "URL CAM"]
        if not all(col in df_excel.columns for col in required_columns):
            return pd.DataFrame()

        for index, row in df_excel.iterrows():
            lat = float(row["LATWGS84"]) if pd.notna(row["LATWGS84"]) else 0.0
            lon = float(row["LONWGS84"]) if pd.notna(row["LONWGS84"]) else 0.0
            url_image = str(row["URL CAM"]) if pd.notna(row["URL CAM"]) else ""

            if not (43.0 <= lat <= 43.4 and -2.49 <= lon <= -1.7):
                continue

            camaras_data.append({
                "id": f"excel_cam_{index}",
                "name": f"Cámara {index}",
                "url_image": url_image,
                "lat": lat,
                "lon": lon,
            })

    except Exception as e:
        print(f"ERROR leyendo {EXCEL_PATH}: {e}")

    return pd.DataFrame(camaras_data)

def generar_mapa_trafico():
    df = obtener_camaras_trafico()

    fig = Figure(width=1000, height=800)
    m = folium.Map(location=[43.268, -2.195], zoom_start=10)
    fig.add_child(m)

    for _, row in df.iterrows():
        popup = f"<b>{row['name']}</b><br>"
        if row["url_image"]:
            popup += f'<img src="{row["url_image"]}" width="200" onerror="this.src=\'https://placehold.co/200x150/cccccc/000000?text=No+Image\'">'
        popup += f"<br>Lat: {row['lat']}<br>Lon: {row['lon']}"
        folium.Marker(
            location=[row["lat"], row["lon"]],
            tooltip=row["name"],
            popup=folium.Popup(popup, max_width=300),
            icon=folium.Icon(color="blue", icon="video-camera", prefix='fa')
        ).add_to(m)

    return m.get_root().render()

def layout():
    return html.Div([
         html.Div([
              html.H1("Mapa de Cámaras de Tráfico en Gipuzkoa", style={
                "textAlign": "center",
                "color": "black",
                "fontSize": "2rem",
                "marginBottom": "15px",
            }),
        html.P([
                "Este mapa muestra las cámaras de tráfico disponibles en Gipuzkoa. "
                "Cada marcador indica la ubicación de una cámara y permite visualizar la imagen"
                "en tiempo real si está disponible. Para ver la imagen con claridad, haga click derecho encima de la imagen y seleccione 'Abrir imagen en una nueva pestaña' ",
                "Para más información, puede encontrar los datos en: ",
                html.A(
                    "opendata.euskadi.eus",
                    href="https://opendata.euskadi.eus/catalogo/-/camaras-de-trafico-de-euskadi/",
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
            id="loading-traffic",
            type="circle",
            children=[
                html.Iframe(
                    id='mapa-trafico',
                    srcDoc=generar_mapa_trafico(),
                    width='100%',
                    height='800px',
                    style={'border': 'none'}
                ),
                dcc.Interval(
                    id='interval-traffic-component',
                    interval=10 * 60 * 1000,  # cada 10 minutos
                    n_intervals=0
                )
            ]
        ),
    ])
def register_callbacks(app):
    @app.callback(
        Output('mapa-trafico', 'srcDoc'),
        Input('interval-traffic-component', 'n_intervals')
    )
    def update_map(_):
        return generar_mapa_trafico()

