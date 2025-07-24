import requests
from lxml import etree
import folium
import dash
from dash import dcc, html
from branca.element import Figure
import pandas as pd


def obtener_poligono_zbe():
    url = "https://infocar.dgt.es/datex2/v3/dgt/zbe/ControledZonePublication/Donostia-SanSebastian.xml"
    response = requests.get(url)
    if response.status_code != 200:
        print("No se pudo descargar el XML")
        return []

    root = etree.fromstring(response.content)

    coords_elements = root.xpath('//*[local-name()="openlrCoordinates"]')
    coords = []
    for elem in coords_elements:
        lat_nodes = elem.xpath('.//*[local-name()="latitude"]')
        lon_nodes = elem.xpath('.//*[local-name()="longitude"]')
        if lat_nodes and lon_nodes:
            lat = float(lat_nodes[0].text)
            lon = float(lon_nodes[0].text)
            coords.append((lat, lon))

    return coords


def crear_mapa_zbe(coords):
    if not coords:
        return None

    centro_lat = sum(lat for lat, _ in coords) / len(coords)
    centro_lon = sum(lon for _, lon in coords) / len(coords)

    fig = Figure(width=1000, height=800)
    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=15)
    fig.add_child(m)

    folium.Polygon(
        locations=coords + [coords[0]],  
        color='green',
        weight=3,
        fill=True,
        fill_opacity=0.3,
        popup="Zona de Bajas Emisiones - Donostia"
    ).add_to(m)

    return m.get_root().render()


coords_zbe = obtener_poligono_zbe()
mapa_html = crear_mapa_zbe(coords_zbe)

layout = html.Div([
    html.Div([
        html.H1("Mapa de Zona de Bajas Emisiones (ZBE) en Donostia", style={
            "textAlign": "center",
            "color": "black",
            "fontSize": "2rem",
            "marginBottom": "1px"
        }),
        html.P([
        "Este mapa muestra la Zona de Bajas Emisiones (ZBE) de Donostia. "
        "El polígono en verde representa los límites de la zona controlada. "
        "Los vehículos que no cumplen con los requisitos de emisiones establecidos tienen restringido el acceso o el aparcamiento en esta zona. ",
        "Para más información, puede encontrar los datos en: ",
        html.A(
                "infocar.dgt.es",
                href="https://infocar.dgt.es/datex2/v3/dgt/zbe/ControledZonePublication/",
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
    dcc.Loading(
        id="loading-zbe",
        type="circle",
        fullscreen=False,
        children=html.Iframe(
            id='mapa-zbe',
            srcDoc=mapa_html,
            width='100%',
            height='900px',
            style={'border': 'none'}
        )
    )
], style={"margin": "0", "padding": "0", "position": "relative"})

def obtener_zbe_coords():
    coords = obtener_poligono_zbe()
    df = pd.DataFrame(coords, columns=["latitude", "longitude"])
    return df