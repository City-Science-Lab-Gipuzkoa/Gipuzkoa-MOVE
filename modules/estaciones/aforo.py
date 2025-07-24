from dash import dcc, html, Output, Input
import pandas as pd
import folium
import dash
import os
import base64
from branca.element import Figure
from branca.element import Figure, MacroElement
from jinja2 import Template

BASE_PATH = os.path.join(os.path.dirname(__file__), "../../data/estaciones")

estaciones_df = pd.read_csv(os.path.join(BASE_PATH, "estaciones.csv"), sep=";", encoding="ISO-8859-1")
estaciones_df["Latitud"] = estaciones_df["Latitud"].str.replace(",", ".").astype(float)
estaciones_df["Longitud"] = estaciones_df["Longitud"].str.replace(",", ".").astype(float)
estaciones_df = estaciones_df.rename(columns={"ETD code": "Estacion"})

rsu_info = pd.read_excel(os.path.join(BASE_PATH, "RSU_data.xlsx"))
rsu_info["latitude"] = rsu_info["latitude"].astype(str).str.replace(",", ".").astype(float)
rsu_info["longitude"] = rsu_info["longitude"].astype(str).str.replace(",", ".").astype(float)

def generar_mapa_html(semana_num):
    año = 2025
    semana = f"Semana_{semana_num}-{año}"
    output_dir_estaciones = os.path.join(BASE_PATH, f"FlujoVehiculos_{semana}")
    output_dir_rsu = os.path.join(BASE_PATH, f"FlujoVehiculos_Semana_{semana_num}-{año}")

    fig = Figure(width=1000, height=800)
    m = folium.Map(location=[43.0, -2.0], zoom_start=8, control_scale=False, tiles=None)
    folium.TileLayer(tiles='OpenStreetMap', attr='', name='OSM', control=False).add_to(m)
    fig.add_child(m)

    for est in estaciones_df.itertuples():
        lat = est.Latitud
        lon = est.Longitud
        estacion_id = est.Estacion
        municipio = est.Municipality
        carretera = est.System

        nombre_archivo = f"Estacion_{estacion_id}_{carretera}_{municipio}.png"
        nombre_archivo = nombre_archivo.replace(" ", "_").replace("/", "-").replace("\\", "-")
        ruta_imagen = os.path.join(output_dir_estaciones, nombre_archivo)

        if os.path.exists(ruta_imagen):
            with open(ruta_imagen, 'rb') as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            html_img = f'<img src="data:image/png;base64,{img_base64}" style="display:block; max-width:100%; height:auto;">'
            iframe = folium.IFrame(html_img, width=800, height=700)
            popup = folium.Popup(iframe, max_width=410, max_height=300)

            folium.Marker(
                location=[lat, lon],
                popup=popup,
                tooltip=f'Estación {estacion_id}',
                icon=folium.Icon(color="blue")
            ).add_to(m)
        else:
            folium.Marker(
                location=[lat, lon],
                tooltip=f'Estación {estacion_id} (Sin datos esta semana.)',
                icon=folium.Icon(color="red")
            ).add_to(m)

    for _, rsu in rsu_info.iterrows():
        lat = rsu["latitude"]
        lon = rsu["longitude"]
        rsu_id = rsu["RSU"]
        nombre = rsu.get("Name", rsu_id)

        nombre_archivo = f"RSU_{rsu_id}_Semana_{semana_num}.png"
        ruta_imagen = os.path.join(output_dir_rsu, nombre_archivo)
        print(f"Comprobando imagen RSU: {ruta_imagen} - Existe? {os.path.exists(ruta_imagen)}")

        if os.path.exists(ruta_imagen):
            with open(ruta_imagen, 'rb') as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            html_img = f'<img src="data:image/png;base64,{img_base64}" style="display:block; max-width:100%; height:auto;">'
            iframe = folium.IFrame(html_img, width=800, height=700)
            popup = folium.Popup(iframe, max_width=410, max_height=300)

            folium.Marker(
                location=[lat, lon],
                popup=popup,
                tooltip=f'{rsu_id} - {nombre}',
                icon=folium.Icon(color="green")
            ).add_to(m)
    legend_html = """
    <div style="    
        position: fixed;
        top: 10px; right: 10px;
        z-index: 1000;
        background-color: white;
        padding: 10px;
        border: 2px solid grey;
        border-radius: 8px;
        font-size: 14px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
    ">
        <div style="margin-top: 6px;">
            <div style="display: flex; align-items: center;">
                <div style="width: 12px; height: 20px; background-color: #00CCFF; border-radius: 2px; margin-right: 6px;"></div>
                Estaciones de aforo (espiras)
            </div>
            <div style="display: flex; align-items: center; margin-top: 4px;">
                <div style="width: 12px; height: 20px; background-color: green; border-radius: 2px; margin-right: 6px;"></div>
                RSU
            </div>
            <div style="display: flex; align-items: center; margin-top: 4px;">
                <div style="width: 12px; height: 20px; background-color: red; border-radius: 2px; margin-right: 6px;"></div>
                Estaciones de aforo sin datos esta semana
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
            html.H1("Mapa de Parkings Públicos en Donostia", style={
                "textAlign": "center",
                "color": "black",
                "fontSize": "2rem",
                "marginBottom": "15px",
            }),
            html.P([
            "Este mapa muestra la ubicación de las estaciones de aforo de tráfico (espiras) y las RSU desplegadas en Gipuzkoa "
            "Cada marcador representa una estación o unidad concreta: las estaciones de aforo (en azul) y  las RSU (en verde). "
            "Al hacer clic en cada marcador, se visualiza una gráfica correspondiente a esa semana específica, con los patrones de tráfico registrados. Las espiras sin datos disponibles en la semana seleccionada aparecen en rojo. Puedes seleccionar distintas semanas para explorar cómo varía el tráfico en el territorio. ",
            "Para más información, puede encontrar los datos relacionados con las espiras (los datos de las RSU son privados) en: ",
                html.A(
                    "gipuzkoairekia.eus",
                    href="https://urretxu.gipuzkoairekia.eus/es/web/guest/datu-irekien-katalogoa/-/openDataSearcher/detail/detailView/07c8a249-c1ba-4a77-bed3-d174980f652e",
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
    
    html.Div([
        html.Button(f"Semana {i}", id=f"btn-{i}", n_clicks=0) for i in range(2, 22)
    ], style={"display": "flex", "flexWrap": "wrap", "gap": "10px", "marginBottom": "20px"}),

    dcc.Loading(
        id="loading",
        type="circle",
        fullscreen=False,
        children=html.Iframe(
            id='mapa-aforo',
            srcDoc=generar_mapa_html(2),
            width='100%',
            height='1000px',
            style={'border': 'none'}
        )
    )
])

def register_callbacks(app):
    @app.callback(
        Output('mapa-aforo', 'srcDoc'),
        [Input(f'btn-{i}', 'n_clicks') for i in range(2, 22)]
    )
    def actualizar_mapa(*n_clicks):
        ctx = dash.callback_context
        semana_activa = 12  
        if ctx.triggered:
            boton_id = ctx.triggered[0]['prop_id'].split('.')[0]
            semana_activa = int(boton_id.split('-')[1])
        return generar_mapa_html(semana_activa)
