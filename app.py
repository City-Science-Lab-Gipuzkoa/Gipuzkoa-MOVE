from dash import Dash, dcc, html, Input, State, Output, dash_table, ctx
import modules.dgt.electrolineras as electrolineras
import modules.udala.ota as ota
import modules.udala.zbe as zbe
import modules.udala.parkings as parkings
import modules.gasolineras.gasolineras as gasolineras
import modules.attg.autobuses as autobuses
import modules.dgt.incidencias as incidencias
import modules.aemet.aemet as estaciones
import modules.estaciones.aforo as aforo
import modules.custom.mapa_custom as ia
import modules.rsu.rsu as rsu
import modules.dgt3.dgt3 as dgt3
import pandas as pd
import os
import smtplib
from email.message import EmailMessage
from flask import send_file

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# Tarjeta reutilizable
def crear_tarjeta(titulo, descripcion, enlace, download_id, boton_id):
    return html.Div([
        html.H3(titulo),
        html.P(descripcion),
        html.Div([
            html.A("Ver más →", href=enlace, target="_self", className="ver-mapa"),
            html.Button("Descargar datos", id=boton_id, className="ver-mapa", n_clicks=0) if download_id else None,
            dcc.Download(id=download_id) if download_id else None
        ], style={"display": "flex", "gap": "10px"})
    ], className="tarjeta")


# ========================
# HOME PRINCIPAL
# ========================
home_principal_layout = html.Div([
    html.Div([
        html.H1("Fuentes de datos de movilidad en Gipuzkoa", className="titulo-principal"),
        html.P("Bienvenido a la Fuente de Datos de Movilidad en Gipuzkoa, una plataforma integral para explorar, analizar y visualizar diversos conjuntos de datos de movilidad en Gipuzkoa."), 
        html.P("¡Explore y descubra los datos disponibles!"),
        html.Hr()
    ], className="cabecera"),

    html.Div([
        crear_tarjeta(
            "Catálogo de fuentes de datos",
            "Excel con inventario de fuentes, sensores y metadatos.",
            "/excel",
            None,
            None
        ),
        crear_tarjeta(
            "Visor de mapas de movilidad",
            "Visualización interactiva de datos públicos.",
            "/app",
            None,
            None
        )
    ], className="grid"),

    html.Div([
        html.Img(src="/assets/logos/tecnun-1.png", className="logo-footer")
    ], className="footer")
])


# ========================
# HOME DE LA APP (VISOR)
# ========================
home_layout = html.Div([
    html.Div([
        html.Div([
            html.A("← Volver", href="/", className="volver"),
            html.H1("Visor de movilidad de Guipúzcoa", className="titulo-centro"),
        ], className="cabecera-linea"),
        html.P(
            "Explore mapas interactivos con información actualizada sobre movilidad, "
            "zonas OTA, gasolineras, parkings y otros recursos en Gipuzkoa.",
            className="descripcion-visormovilidad"
        ),
        html.Hr()
    ], className="cabecera"),

    html.Div([
        crear_tarjeta("Electrolineras", "Electrolineras y puntos de recarga.", "/mapa/electrolineras", None, None),
        crear_tarjeta("OTA", "Zonas OTA y restricciones de aparcamiento en Donostia.", "/mapa/ota", None, None),
        crear_tarjeta("ZBE", "Zona de bajas emisiones en Donostia.", "/mapa/zbe", None, None),
        crear_tarjeta("Gasolineras", "Gasolineras y precios.", "/mapa/gasolineras", None, None),
        crear_tarjeta("Autobuses", "Rutas urbanas e interurbanas.", "/mapa/autobuses", None, None),
        crear_tarjeta("Cámaras de tráfico", "Cámaras en tiempo real.", "/mapa/incidencias", None, None),
        crear_tarjeta("Estaciones meteorológicas", "Estaciones AEMET y datos en tiempo real.", "/mapa/estaciones", None, None),
        crear_tarjeta("Estaciones de aforo", "Espiras y RSU con gráficas.", "/mapa/aforo", None, None),
        crear_tarjeta("Parkings", "Plazas libres en Donostia en tiempo real.", "/mapa/parkings", None, None)
    ], className="grid"),

    html.Div([
        html.A([
            html.Img(
                src="/assets/robot-ia.gif",  
                style={
                    "width": "80px",
                    "height": "80px",
                    "borderRadius": "50%",
                    "boxShadow": "0 4px 10px rgba(0,0,0,0.3)",
                    "cursor": "pointer",
                    "transition": "transform 0.2s ease"
                },
                id="boton-robot-ia"
            ),
            html.Div(
                "¡Clickeame para generar tu propio mapa!",
                id="tooltip-text",
                style={
                    "visibility": "hidden",
                    "width": "160px",
                    "backgroundColor": "rgba(60, 60, 60, 0.9)",
                    "color": "#fff",
                    "textAlign": "center",
                    "borderRadius": "10px",
                    "padding": "8px 12px",
                    "position": "absolute",
                    "bottom": "100%",
                    "right": "50%",
                    "transform": "translateX(50%)",
                    "marginBottom": "10px",
                    "fontSize": "13px",
                    "boxShadow": "0 2px 10px rgba(0,0,0,0.3)",
                    "zIndex": "10000",
                    "whiteSpace": "normal",
                    "pointerEvents": "none"
                }
            )
        ], href="/mapa/ia", style={
            "textDecoration": "none",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "position": "relative"
        }, id="boton-robot-container")
    ], style={
        "position": "fixed",
        "bottom": "20px",
        "right": "50px",
        "zIndex": "9999",
        "backgroundColor": "transparent",  # sin fondo para que el tooltip se vea bien
        "padding": "10px",
        "userSelect": "none"
    }),

    html.Div([
        html.Img(src="/assets/logos/tecnun-1.png", className="logo-footer")
    ], className="footer")
])


# Diccionario de layouts de mapas
mapas = {
    'electrolineras': electrolineras.layout,
    'ota': ota.layout,
    'zbe': zbe.layout,
    'gasolineras': gasolineras.layout,
    'incidencias': incidencias.layout,
    'autobuses': autobuses.layout_fn(app),
    'estaciones': estaciones.layout,
    'aforo': aforo.layout,
    'parkings': parkings.layout,
    'ia': ia.layout
}

pages = {
    "rsu": rsu.layout,
    "dgt3": dgt3.layout
}

# Layout general
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


# Enrutamiento
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/' or pathname == '/home':
        return home_principal_layout
    elif pathname == '/app':
        return home_layout
    elif pathname.startswith('/mapa/'):
        mapa_key = pathname.split('/mapa/')[-1]
        if mapa_key in mapas:
            contenido = mapas[mapa_key]() if callable(mapas[mapa_key]) else mapas[mapa_key]
            return html.Div([
                html.A("← Volver", href="/app", className="volver"),
                contenido
            ], className="contenedor-mapa")
        else:
            return html.H3("Mapa no encontrado.")
    elif pathname == '/pages/rsu':
        return html.Div([
            html.A("← Volver", href="/excel", className="volver"),
            pages["rsu"] 
        ], className="contenedor-mapa")
    elif pathname == '/pages/dgt3':
        return html.Div([
            html.A("← Volver", href="/excel", className="volver"),
            pages["dgt3"] 
        ], className="contenedor-mapa")
    elif pathname == '/excel':
        ruta_excel = os.path.join("data/excel", "Espacios de datos.xlsx")
        df_excel = pd.read_excel(ruta_excel)
        if "Acceso a los datos" in df_excel.columns:
            df_excel["Acceso a los datos"] = df_excel["Acceso a los datos"].apply(
                lambda x: f"[Acceder]({x})" if pd.notna(x) and str(x).strip() != "" else "Sin enlace"
            )
        def obtener_estado_descarga(row_id):
            carpeta = "data/muestras"
            formatos = ["csv", "xlsx", "zip", "txt"]
            for ext in formatos:
                ruta_archivo = os.path.join(carpeta, f"muestra_{row_id}.{ext}")
                if os.path.exists(ruta_archivo):
                    return f"[Descargar](./descarga_muestra/{row_id})"
            return "Descarga no disponible"

        df_excel["Descargar muestra"] = [obtener_estado_descarga(i) for i in range(len(df_excel))]
        return html.Div([
        html.A("← Volver", href="/", className="volver"),
        html.H2("Catálogo de fuentes de datos"),
        html.P("Puede consultar aquí el archivo Excel con las fuentes de datos utilizadas en el estudio."),
        dash_table.DataTable(
            id='tabla-excel',
            data=df_excel.to_dict("records"),
            columns=[
                *[
                    {"name": col, "id": col, "presentation": "markdown"} if col == "Acceso a los datos" else {"name": col, "id": col}
                    for col in df_excel.columns if col != 'Descargar muestra'
                ],
                {"name": "Descargar muestra", "id": "Descargar muestra", "presentation": "markdown"}
            ],
            page_size=15,
            filter_action="native",
            sort_action="native",
            style_table={
                'overflowX': 'auto',        
                'overflowY': 'auto',
                'maxHeight': '600px',
                'minWidth': '700px',          
                'maxWidth': '95vw',           
                'margin': '0 auto',           
                'border': '1px solid #ccc',
                'borderRadius': '10px',
                'boxShadow': '0px 4px 10px rgba(0,0,0,0.05)'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '6px',
                'minWidth': '120px',
                'whiteSpace': 'normal',
                'fontFamily': "'Segoe UI', sans-serif",
                'fontSize': '13px'
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'position': 'sticky',
                'top': 0,
                'zIndex': 1
            },
            fixed_columns={'headers': True, 'data': 1},
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f9f9f9'
                }
            ]
        ),
        html.Div(style={"height": "20px"}),  # Espacio entre tabla y botón
        html.P("Para más información, puede descargar el catálogo de datos entero. Si ha encontrado una fuente de datos de movilidad que no aparezca en el catálogo, ¡contacte con nosotros!"),
         html.Div([
            html.Button("Descargar Excel", id="btn-excel", className="ver-mapa", n_clicks=0, style={
                "backgroundColor": "green",
                "color": "white",
                "border": "none",
                "borderRadius": "6px",
                "padding": "5px 10px",
                "fontSize": "14px",
                "cursor": "pointer",
                "boxShadow": "0 2px 6px rgba(0, 0, 0, 0.15)"
            }),
            html.Button("📩 Contactar", id="btn-contactar", n_clicks=0, style={
                "backgroundColor": "#ffc107",
                "color": "black",
                "padding": "5px 10px",
                "border": "none",
                "borderRadius": "6px",
                "fontSize": "14px",
                "marginTop": "10px",
                "marginLeft": "10px",
                "cursor": "pointer"
            }, disabled=False),
            html.Div(
                id="formulario-contacto-modal2",
                style={
                    "display": "none",  
                    "position": "fixed",
                    "backgroundColor": "white",  
                    "top": "40%",
                    "left": "50%",
                    "transform": "translate(-50%, -50%)",
                    "zIndex": 9999,
                    "borderRadius": "12px",
                    "overflowY": "auto", 
                    "maxWidth": "500px",
                    "margin": "50px auto",  
                    "boxShadow": "0 4px 12px rgba(0,0,0,0.15)",
                    "boxSizing": "border-box",
                },
                children=[
                    html.Div(
                        id="formulario-contacto",
                        style={
                            "backgroundColor": "white",
                            "padding": "25px",
                            "borderRadius": "10px",
                            "boxShadow": "0 6px 18px rgba(0,0,0,0.1)",
                            "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                        },
                        children=[
                            html.H4("Formulario de contacto", style={"color": "#222", "textAlign": "center", "marginBottom": "25px", "fontWeight": "600", "fontSize": "2rem"}),
                            html.P("Si ha encontrado una fuente de datos de movilidad que no aparezca en el catálogo, rellene este formulario. ¡Lo valoraremos!", style={"color": "black", "textAlign": "center", "marginBottom": "25px", "fontWeight": "600", "fontSize": "0.8rem"}),
                            dcc.Input(id="input-nombre", type="text", placeholder="Nombre y Apellidos", style={
                                "width": "100%", "marginBottom": "15px", "padding": "8px", "fontSize": "0.9rem", "borderRadius": "6px", "border": "1px solid #ccc", "outline": "none",
                            }),
                            dcc.Input(id="input-email", type="email", placeholder="Email", style={
                                "width": "100%", "marginBottom": "15px", "padding": "8px", "fontSize": "0.9rem", "borderRadius": "6px", "border": "1px solid #ccc", "outline": "none",
                            }),
                            dcc.Input(id="input-nombrefuente", type="text", placeholder="Nombre de la fuente de datos", style={
                                "width": "100%", "marginBottom": "15px", "padding": "8px", "fontSize": "0.9rem", "borderRadius": "6px", "border": "1px solid #ccc", "outline": "none",
                            }),
                            dcc.Input(id="input-link", type="text", placeholder="Link al repositorio de los datos ('Datos Privados')", style={
                                "width": "100%", "marginBottom": "15px", "padding": "8px", "fontSize": "0.9rem", "borderRadius": "6px", "border": "1px solid #ccc", "outline": "none",
                            }),
                            dcc.Textarea(id="input-mensaje", placeholder="Información relevante acerca de los datos.", style={
                                "width": "100%", "height": "80px", "padding": "8px", "marginBottom": "20px", "fontSize": "0.9rem", "borderRadius": "6px", "border": "1px solid #ccc", "outline": "none", "resize": "vertical",
                            }),

                            html.Div([
                                html.Button("Enviar formulario", id="btn-enviar-formulario", n_clicks=0, style={
                                    "backgroundColor": "green",
                                    "color": "white",
                                    "padding": "10px 20px",
                                    "border": "none",
                                    "borderRadius": "6px",
                                    "fontSize": "0.9rem",
                                    "cursor": "pointer",
                                    "marginRight": "10px",
                                    "transition": "background-color 0.3s ease",
                                }),
                                html.Button("Cerrar", id="btn-cerrar-modal", n_clicks=0, style={
                                    "backgroundColor": "#6c757d",
                                    "color": "white",
                                    "padding": "10px 20px",
                                    "border": "none",
                                    "borderRadius": "6px",
                                    "fontSize": "0.9rem",
                                    "cursor": "pointer",
                                    "transition": "background-color 0.3s ease",
                                }),
                            ], style={"textAlign": "center"}),

                            html.Div(id="mensaje-envio2", style={"marginTop": "15px", "color": "green", "textAlign": "center", "fontWeight": "600"}),

                            html.Div([
                            html.Hr(style={"margin": "20px 0"}),
                            html.Div([
                                html.P("Política de Privacidad", style={"fontSize": "13px", "color": "#666", "marginRight": "20px", "cursor": "pointer"}),
                                html.P("Términos y Condiciones", style={"fontSize": "13px", "color": "#666", "cursor": "pointer"}),
                            ], style={"display": "flex", "justifyContent": "center", "gap": "15px"}),
                        ]),
                        ]
                    )
                ]
            ),
        ]),
        dcc.Download(id="dl-excel")
        ], className="contenedor-mapa")
    else:
        return html.H3("Página no encontrada.")
    
# === Callbacks de descarga ===
@app.callback(
    Output("dl-excel", "data"),
    Input("btn-excel", "n_clicks"),
    prevent_initial_call=True
)
def descargar_excel(n):
    ruta = os.path.join("data/excel", "Espacios de datos.xlsx")
    return dcc.send_file(ruta)

@app.server.route("/descarga_muestra/<int:row_id>")
def descargar_muestra(row_id):
    carpeta = "data/muestras"
    formatos = ["csv", "xlsx", "zip", "txt"]
    for ext in formatos:
        ruta_archivo = os.path.join(carpeta, f"muestra_{row_id}.{ext}")
        if os.path.exists(ruta_archivo):
            return send_file(ruta_archivo, as_attachment=True)
    return "Archivo no encontrado", 404

@app.callback(
    Output("mensaje-envio2", "children"),
    Input("btn-enviar-formulario", "n_clicks"),
    State("input-nombre", "value"),
    State("input-email", "value"),
    State("input-nombrefuente", "value"),
    State("input-link", "value"),
    State("input-mensaje", "value"),
    prevent_initial_call=True
)
def enviar_formulario(n_clicks, nombre, email, nombre_fuente, link, mensaje):
    if not nombre or not email or not mensaje:
        return "Por favor, rellene todos los campos obligatorios."

    try:
        msg = EmailMessage()
        msg["Subject"] = "Nuevo formulario de contacto - Catalogo Datos"
        msg["From"] = email
        msg["To"] = "mzuazolaarr@alumni.unav.es"
        cuerpo = f"""
        Nombre: {nombre}
        Email: {email}
        Nombre de la fuente: {nombre_fuente}
        Link: {link}
        Mensaje: {mensaje}
        """
        msg.set_content(cuerpo)

        # Configuración SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login('appdatosmovilidad@gmail.com', 'wovz ejwt xkfd amzg')
            smtp.send_message(msg)

        return "¡Formulario enviado correctamente! Gracias por su colaboración."

    except Exception as e:
        print("Error enviando email:", e)
        return "❌ Ha ocurrido un error al enviar el formulario."


@app.callback(
Output("formulario-contacto-modal2", "style"),
Input("btn-contactar", "n_clicks"),
Input("btn-cerrar-modal", "n_clicks"),
State("formulario-contacto-modal2", "style"),
prevent_initial_call=True
)
def toggle_modal(n_clicks_open, n_clicks_close, current_style):
    trigger = ctx.triggered_id
    if trigger == "btn-contactar":
        return {**current_style, "display": "flex"}
    elif trigger == "btn-cerrar-modal":
        return {**current_style, "display": "none"}
    return current_style

# Callbacks de módulos
aforo.register_callbacks(app)
parkings.register_callbacks(app)
ia.register_callbacks(app)
rsu.register_callbacks(app)
dgt3.register_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True)
