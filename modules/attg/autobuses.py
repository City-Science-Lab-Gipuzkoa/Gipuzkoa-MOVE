from dash import dcc, html, Output, Input
import pandas as pd
import os
import folium
from branca.element import Figure

BASE_PATH = os.path.join(os.path.dirname(__file__), "../../data/attg")
carpetas = [d for d in os.listdir(BASE_PATH) if d.startswith("l_") or d == "dbus"]

layout = html.Div(style={
    'margin': '0',
    'padding': '0',
    'height': '100vh',
    'width': '100vw',
    'position': 'relative',
    'overflow': 'hidden',
    'fontFamily': 'Arial, sans-serif',
}, children=[

    html.Div([
        
        html.H1("Mapa Interactivo de Autobuses en Gipuzkoa", style={
        "textAlign": "center",
        "color": "black",
        "fontSize": "2rem",
        "marginBottom": "5px",
        }),

        html.P([
        "Este mapa muestra las rutas de autobuses disponibles en Gipuzkoa. "
        "Puedes explorar las líneas de autobús según la localidad seleccionada, "
        "visualizando sus trayectos y paradas en el mapa interactivo. "
        "Los marcadores indican las paradas de autobús a lo largo de cada ruta. ",
        "Para más información, puede encontrar los datos en: ",
            html.A(
                "geo.euskadi.eus",
                href="https://www.geo.euskadi.eus/cartografia/DatosDescarga/Transporte/Moveuskadi/ATTG/",
                target="_blank",
                style={"color": "#007BFF", "textDecoration": "underline"}
            )],
        style={
            "textAlign": "center",
            "color": "black",
            "fontSize": "16px",
            "fontFamily": "'Segoe UI', sans-serif",
            "marginBottom": "10px",
            "marginTop": "15px",
        }
    ),
        html.Label("Localidad:", style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id='dropdown-localidad',
            options=[{'label': carpeta, 'value': carpeta} for carpeta in carpetas],
            value=carpetas[0] if carpetas else None,
            style={'marginBottom': '10px'}
        ),
        html.Label("🚏 Línea de Bus:", style={'fontWeight': 'bold'}),
        dcc.Dropdown(id='dropdown-linea'),
        html.Label("Dirección:", style={'fontWeight': 'bold'}),
        dcc.Dropdown(id='dropdown-direccion'),
    ], style={
        'position': 'absolute',
        'top': '20px',
        'right': '80px',
        'width': '420px',
        'zIndex': '900',
        'backgroundColor': '#ffffffee',
        'padding': '15px',
        'borderRadius': '10px',
        'boxShadow': '0 4px 10px rgba(0,0,0,0.15)',
    }),

    html.Iframe(id='mapa', style={
        'position': 'absolute',
        'top': '0',
        'left': '0',
        'width': '100%',
        'height': '100%',
        'border': 'none',
    })
])

def register_callbacks(app):
    @app.callback(
        Output('dropdown-linea', 'options'),
        Output('dropdown-linea', 'value'),
        Input('dropdown-localidad', 'value')
    )
    def actualizar_lineas(localidad):
        ruta = os.path.join(BASE_PATH, localidad, 'routes.txt')
        if os.path.exists(ruta):
            df = pd.read_csv(ruta)
            opciones = [{'label': f"{row['route_short_name']} - {row['route_long_name']}", 'value': row['route_id']} for _, row in df.iterrows()]
            return opciones, opciones[0]['value'] if opciones else None
        return [], None
    @app.callback(
        Output('dropdown-direccion', 'options'),
        Output('dropdown-direccion', 'value'),
        Input('dropdown-localidad', 'value'),
        Input('dropdown-linea', 'value')
    )
    def actualizar_direcciones(localidad, linea):
        if not linea:
            return [], None
        ruta_base = os.path.join(BASE_PATH, localidad)
        trips_path = os.path.join(ruta_base, "trips.txt")
        if not os.path.exists(trips_path):
            return [], None

        trips = pd.read_csv(trips_path)
        trips_filtrados = trips[trips['route_id'] == int(linea)]
        direcciones_unicas = trips_filtrados['direction_id'].dropna().unique()
        opciones = []
        for d in sorted(direcciones_unicas):
            if int(d) == 0:
                label = "Dirección Ida"
            elif int(d) == 1:
                label = "Dirección Vuelta"
            else:
                label = f"Dirección {int(d)}"
            opciones.append({'label': label, 'value': int(d)})

        if opciones:
            return opciones, opciones[0]['value']
        else:
            return [{'label': 'Dirección Ida', 'value': 0}], 0

    @app.callback(
        Output('mapa', 'srcDoc'),
        Input('dropdown-localidad', 'value'),
        Input('dropdown-linea', 'value'),
        Input('dropdown-direccion', 'value')
    )
    def actualizar_mapa(localidad, linea, direccion):
        if not linea or direccion is None:
            return ""

        ruta_base = os.path.join(BASE_PATH, localidad)

        try:
            routes = pd.read_csv(os.path.join(ruta_base, "routes.txt"))
            trips = pd.read_csv(os.path.join(ruta_base, "trips.txt"))
            stop_times = pd.read_csv(os.path.join(ruta_base, "stop_times.txt"))
            stops = pd.read_csv(os.path.join(ruta_base, "stops.txt"))
            shapes = pd.read_csv(os.path.join(ruta_base, "shapes.txt"))

            trips_filtrados = trips[(trips['route_id'] == int(linea)) & (trips['direction_id'] == int(direccion))]
            if trips_filtrados.empty:
                return "<p>No hay datos para esa línea y dirección.</p>"

            trip_id = trips_filtrados.iloc[0]['trip_id']
            shape_id = trips_filtrados.iloc[0]['shape_id']

            shape_df = shapes[shapes['shape_id'] == shape_id].sort_values("shape_pt_sequence")
            lat_lon_shape = list(zip(shape_df["shape_pt_lat"], shape_df["shape_pt_lon"]))

            stop_times_df = stop_times[stop_times["trip_id"] == trip_id]
            stop_ids = stop_times_df["stop_id"].unique()
            stops_df = stops[stops["stop_id"].isin(stop_ids)]

            centro_mapa = lat_lon_shape[len(lat_lon_shape)//2] if lat_lon_shape else (43.3, -1.98)
            fig = Figure(width=1000, height=800)
            m = folium.Map(location=centro_mapa, zoom_start=13)
            fig.add_child(m)

            if lat_lon_shape:
                folium.PolyLine(lat_lon_shape, color="blue", weight=5, opacity=0.8).add_to(m)

            for _, stop in stops_df.iterrows():
                folium.Marker(
                    location=[stop["stop_lat"], stop["stop_lon"]],
                    tooltip=stop["stop_name"],
                    icon=folium.Icon(color='green', icon='bus', prefix='fa')
                ).add_to(m)

            return m.get_root().render()

        except Exception as e:
            return f"<p>Error cargando el mapa: {str(e)}</p>"
        
def layout_fn(app):
    register_callbacks(app)
    return layout
