import dash
from dash import dcc, html
import pandas as pd
import folium
import requests
from branca.element import Figure, MacroElement
from jinja2 import Template
import xml.etree.ElementTree as ET

def obtener_electrolineras():
    url = "https://infocar.dgt.es/datex2/v3/miterd/EnergyInfrastructureTablePublication/electrolineras.xml"
    response = requests.get(url)
    root = ET.fromstring(response.content)

    ns = {
        'd2': 'http://datex2.eu/schema/3/common',
        'd3': 'http://datex2.eu/schema/3/energyInfrastructure',
        'fac': 'http://datex2.eu/schema/3/facilities',
        'loc': 'http://datex2.eu/schema/3/locationReferencing'
    }

    data = []

    for site in root.findall(".//d3:energyInfrastructureSite", ns):
        tipo = site.find("d3:typeOfSite", ns)
        tipo_text = tipo.text if tipo is not None else "NO TIPO"

        loc_ref = site.find("fac:locationReference", ns)
        if loc_ref is None:
            continue

        coords = loc_ref.find("loc:coordinatesForDisplay", ns)
        if coords is None:
            continue

        lat = coords.find("loc:latitude", ns)
        lon = coords.find("loc:longitude", ns)
        if lat is None or lon is None:
            continue

        try:
            lat_val = float(lat.text)
            lon_val = float(lon.text)
        except:
            continue
        if not (43.0 <= lat_val <= 43.4 and -2.8 <= lon_val <= -1.7):
            continue

        name = site.find("fac:name", ns)
        nombre = name.text if name is not None else "Sin nombre"

        data.append({
            "nombre": nombre,
            "lat": lat_val,
            "lon": lon_val,
            "tipo": tipo_text
        })

    return pd.DataFrame(data)

def generar_mapa():
    df = obtener_electrolineras()
    fig = Figure(width=1000, height=800)
    m = folium.Map(location=[43.2, -2.2], zoom_start=10)
    folium.TileLayer('OpenStreetMap').add_to(m)
    fig.add_child(m)

    for _, row in df.iterrows():
        tipo = row["tipo"]
        tipo_lower = tipo.lower()
        color = "green" if tipo_lower == "onstreet" else "blue" if tipo_lower == "openspace" else "orange"

        folium.Marker(
            location=[row["lat"], row["lon"]],
            icon=folium.Icon(color=color, icon="flash", prefix='fa')
        ).add_to(m)

    legend_html = """
    <div style="    
        position: fixed;
        top: 10px; left: 10px;
        z-index: 1000;
        background-color: white;
        padding: 10px;
        border: 2px solid grey;
        border-radius: 8px;
        font-size: 14px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
    ">
        <b>Tipos:</b><br>
        <div style="margin-top: 6px;">
            <div style="display: flex; align-items: center;">
                <div style="width: 12px; height: 20px; background-color: green; border-radius: 2px; margin-right: 6px;"></div>
                En calle (onStreet)
            </div>
            <div style="display: flex; align-items: center; margin-top: 4px;">
                <div style="width: 12px; height: 20px; background-color: blue; border-radius: 2px; margin-right: 6px;"></div>
                Espacio abierto (openSpace)
            </div>
            <div style="display: flex; align-items: center; margin-top: 4px;">
                <div style="width: 12px; height: 20px; background-color: orange; border-radius: 2px; margin-right: 6px;"></div>
                Sin clasificar
            </div>
        </div>
    </div>
    """
    legend = MacroElement()
    legend._template = Template(f"""{{% macro html(this, kwargs) %}}{legend_html}{{% endmacro %}}""")
    m.get_root().add_child(legend)

    return m.get_root().render()

layout = html.Div([
    html.Div([
        html.H1("Mapa de Electrolineras en Gipuzkoa", style={
            "textAlign": "center",
            "color": "black",
            "fontSize": "2rem",
            "marginBottom": "1px"
        }),
        html.P([
            "Este mapa muestra las electrolineras disponibles en Gipuzkoa, clasificadas según su tipo: ",
            "en calle (onStreet), en espacio abierto (openSpace) o sin clasificar. ",
            "Los marcadores están coloreados para facilitar su identificación: verde para electrolineras en calle, azul para espacios abiertos y naranja para las no clasificadas. ",
            "Para más información, puede encontrar los datos en: ",
            html.A(
                "infocar.dgt.es",
                href="https://infocar.dgt.es/datex2/v3/miterd/EnergyInfrastructureTablePublication/",
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
        id="loading",
        type="circle",
        fullscreen=False,
        children=html.Iframe(
            id='mapa',
            srcDoc=generar_mapa(),
            width='100%',
            height='1000px',
            style={'border': 'none'}
        )
    )
], style={"margin": "0", "padding": "0", "position": "relative"})