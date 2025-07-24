import os
import pandas as pd
import folium
from branca.element import Figure
from dash import html

data_folder = os.path.join(os.path.dirname(__file__), "../../data/gasolineras")
archivo_excel = os.path.join(data_folder, "preciosEESS_es.xlsx")

def cargar_datos_gasolineras(ruta_excel):
    df = pd.read_excel(ruta_excel, skiprows=3)
    df = df[df['Provincia'] == 'GIPUZKOA']
    df['Latitud'] = df['Latitud'].str.replace(',', '.').astype(float)
    df['Longitud'] = df['Longitud'].str.replace(',', '.').astype(float)
    df = df.rename(columns={
        'Precio gasolina 95 E5': 'G95',
        'Precio gasóleo A': 'GA'
    })
    return df

def generar_mapa_gasolineras(df):
    fig = Figure(width=1000, height=800)
    m = folium.Map(location=[43.2, -2.2], zoom_start=10)
    fig.add_child(m)

    for _, row in df.iterrows():
        popup = f"""
        <b><u>{row['Rótulo']}</u></b><br>
        {row['Dirección']}<br>
        <b>Gasolina 95:</b> {row.get('G95', 'N/D')} €/L<br>
        <b>Gasóleo A:</b> {row.get('GA', 'N/D')} €/L<br>
        """

        folium.Marker(
            location=[row['Latitud'], row['Longitud']],
            popup=folium.Popup(popup, max_width=250),
            icon=folium.Icon(color="red", icon="tint", prefix="fa")
        ).add_to(m)

    return m.get_root().render()


try:
    df_gasolineras = cargar_datos_gasolineras(archivo_excel)
    mapa_html = generar_mapa_gasolineras(df_gasolineras)
except Exception as e:
    mapa_html = f"<p>Error al cargar los datos de gasolineras: {str(e)}</p>"

layout = html.Div([
    html.Div([
        html.H1("Mapa de Gasolineras en Gipuzkoa", style={
            "textAlign": "center",
            "color": "black",
            "fontSize": "2rem",
            "marginBottom": "1px"
        }),
        html.P([
        "Este mapa interactivo muestra las gasolineras disponibles en Gipuzkoa, incluyendo su ubicación y los precios actuales de gasolina 95 y gasóleo A. ",
        "Para más información, puede encontrar los datos en: ",
            html.A(
                "geoportalgasolineras.es",
                href="https://geoportalgasolineras.es/geoportal-instalaciones/DescargarFicheros",
                target="_blank",
                style={"color": "#007BFF", "textDecoration": "underline"}
            )
        ], style={
            "textAlign": "center",
            "color": "black",
            "fontSize": "16px",
            "fontFamily": "'Segoe UI', sans-serif"
        })
    ], style={"padding": "5px", "borderBottom": "1px solid #ddd"}),

    html.Iframe(srcDoc=mapa_html, width="100%", height="800")
])
