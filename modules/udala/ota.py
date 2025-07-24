import geopandas as gpd
import folium
from branca.element import Template, MacroElement
import os
import dash
from dash import dcc, html
import pandas as pd
import folium
import requests
from jinja2 import Template
import xml.etree.ElementTree as ET

def crear_mapa_ota():
    data_folder = os.path.join(os.path.dirname(__file__), '../../data/udala')

    gdf1 = gpd.read_file(os.path.join(data_folder, "TAO_Bertakoak.shp")).to_crs(epsg=4326)
    gdf2 = gpd.read_file(os.path.join(data_folder, "TAO_Elkarbanatua.shp")).to_crs(epsg=4326)
    gdf3 = gpd.read_file(os.path.join(data_folder, "TAO_Merkataritza.shp")).to_crs(epsg=4326)
    gdf4 = gpd.read_file(os.path.join(data_folder, "TAO_OrdainduBeharrekoEremuak.shp")).to_crs(epsg=4326)

    centro = [43.3183, -1.9812]
    m = folium.Map(location=centro, zoom_start=13)

    colores = {
        "Bertakoak": "red",
        "Elkarbanatua": "purple",
        "Merkataritza": "orange",
        "Ordaintzekoa": "blue"
    }

    for _, row in gdf1.iterrows():
        folium.GeoJson(
            row["geometry"],
            style_function=lambda feature: {
                "fillColor": colores["Bertakoak"],
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.6,
            },
            tooltip=f"Gunea: {row['Gunea']}<br>Info: {row['Ordua']}"
        ).add_to(m)

    for _, row in gdf4.iterrows():
        folium.GeoJson(
            row["geometry"],
            style_function=lambda feature: {
                "fillColor": colores["Ordaintzekoa"],
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.6,
            },
            tooltip=f"Gunea: {row['Gunea']}<br>Info: Tarifa {row['Tarifa']}"
        ).add_to(m)

    for _, row in gdf2.iterrows():
        folium.GeoJson(
            row["geometry"],
            style_function=lambda feature: {
                "color": colores["Elkarbanatua"],
                "weight": 4,
                "opacity": 0.9
            },
            tooltip=f"Gunea: {row['Gunea']}<br>Info: {row['Izena']}"
        ).add_to(m)

    for _, row in gdf3.iterrows():
        folium.GeoJson(
            row["geometry"],
            style_function=lambda feature: {
                "color": colores["Merkataritza"],
                "weight": 4,
                "opacity": 0.9
            },
            tooltip=f"Gunea: {row['Gunea']}<br>Info: {row['Tarifa']}"
        ).add_to(m)

    template = """
    {% macro html(this, kwargs) %}
    <div style="
        position: fixed; 
        bottom: 50px; left: 50px; width: 180px; height: auto; 
        background-color: white;
        border:2px solid grey; 
        z-index:9999; 
        font-size:14px;
        padding: 10px;">
        <b>OTA motak</b><br>
        <div style="margin:2px 0;">
            <span style="background:red;width:15px;height:15px;display:inline-block;margin-right:5px;"></span>
            Bertakoak/Residentes
        </div>
        <div style="margin:2px 0;">
            <span style="background:purple;width:15px;height:15px;display:inline-block;margin-right:5px;"></span>
            Elkarbanatua/Compartido
        </div>
        <div style="margin:2px 0;">
            <span style="background:orange;width:15px;height:15px;display:inline-block;margin-right:5px;"></span>
            Merkataritza/Comercio
        </div>
        <div style="margin:2px 0;">
            <span style="background:blue;width:15px;height:15px;display:inline-block;margin-right:5px;"></span>
            Ordaintzekoa/De pago
        </div>
    </div>
    {% endmacro %}
    """
    macro = MacroElement()
    macro._template = Template(template)
    m.get_root().add_child(macro)

    return m.get_root().render() 

layout = html.Div([
    html.Div([
    html.H1("Mapa de Zonas OTA en Donostia", style={
        "textAlign": "center",
        "color": "black",
        "fontSize": "2rem",
        "marginBottom": "1px"
    }),
    html.P([
        "Este mapa interactivo muestra las diferentes zonas de la OTA (Ordenanza de Tráfico y Aparcamiento) en Donostia, ",
        "clasificadas en cuatro tipos: zonas para residentes (Bertakoak), zonas compartidas (Elkarbanatua), ",
        "zonas comerciales (Merkataritza) y zonas de aparcamiento de pago (Ordaintzekoa). ",
        "Cada tipo está representado con un color distinto para facilitar su identificación. ",
        "Al pasar el cursor sobre cada zona, se muestra información relevante como el nombre del área o la tarifa aplicable. ",
        "Esta herramienta te ayuda a conocer las restricciones y condiciones de aparcamiento en la ciudad. ",
        "Para más información, puede encontrar los datos en: ",
        html.A(
            "donostia.eus - Transporte OTA",
            href="https://www.donostia.eus/datosabiertos/catalogo/transporte-ota",
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
        id="loading-ota",
        type="circle",
        fullscreen=False,
        children=html.Iframe(
            id='mapa-ota',
            srcDoc=crear_mapa_ota(),
            width='100%',
            height='900px',
            style={'border': 'none'}
        )
    )
], style={"margin": "0", "padding": "0", "position": "relative"})
