import os
import pandas as pd
from dash import dcc, html, Input, Output, State, ctx
import dash
from openai import OpenAI
from dash import MATCH
import tempfile
import base64
import io
from dash.exceptions import PreventUpdate
import traceback
import smtplib
from email.message import EmailMessage

# -------------------------------
# Configuración del cliente OpenAI (usando OpenRouter)
# -------------------------------
client = OpenAI(
    api_key="", #INSERT OWN API KEY FROM OPENROUTER
    base_url="https://openrouter.ai/api/v1"
)

def detectar_columnas_lat_lon(df):
    lat_candidates = [c for c in df.columns if 'lat' in c.lower()]
    lon_candidates = [c for c in df.columns if 'lon' in c.lower() or 'lng' in c.lower() or 'long' in c.lower()]
    if lat_candidates and lon_candidates:
        return lat_candidates[0], lon_candidates[0]
    return None, None

def llamar_a_deepseek(df_sample, filename, tmp_path):
    columnas = list(df_sample.columns)
    lat_col, lon_col = detectar_columnas_lat_lon(df_sample)

    texto = df_sample.to_csv(index=False)
    ejemplo_modulo = '''
import os
import pandas as pd
import folium
from branca.element import Figure
from dash import html

data_folder = os.path.join(os.path.dirname(__file__), "../../data/gasolineras")
archivo_excel = os.path.join(data_folder, "preciosEESS_es.xlsx")

def cargar_datos_gasolineras(ruta_excel):
    """
    Lee y procesa el Excel de precios de gasolineras.
    """
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
            icon=folium.Icon(color="blue", prefix="fa")
        ).add_to(m)

    return m.get_root().render()

try:
    df_gasolineras = cargar_datos_gasolineras(archivo_excel)
    mapa_html = generar_mapa_gasolineras(df_gasolineras)
except Exception as e:
    mapa_html = f"<p>Error al cargar los datos de gasolineras: {str(e)}</p>"

layout = html.Div([
    html.Iframe(srcDoc=mapa_html, width="100%", height="800")
])
'''

    prompt = f"""
Estoy creando una aplicación en Dash que permite subir archivos con datos geoespaciales y visualizar un mapa automáticamente usando Folium.

El archivo subido ya está guardado en disco y su ruta completa está disponible en la variable `archivo_excel`. Por tanto, el código debe usar directamente esta variable para cargar el archivo Excel.

Estos son los datos del archivo:

- Nombre archivo: {filename}
- Columnas detectadas: {columnas}
- Ruta temporal del archivo guardado: {tmp_path}
- Columna latitud: {lat_col if lat_col else "No detectada claramente"}
- Columna longitud: {lon_col if lon_col else "No detectada claramente"}

Aquí tienes una muestra de las primeras 10 filas:

{texto}

A continuación tienes un ejemplo de código para otro dataset de gasolineras que usa folium y Dash:

{ejemplo_modulo}

Por favor genera un módulo Python completo compatible con Dash que:

- Use la variable `archivo_excel` para cargar el archivo Excel (sin rutas fijas ni uso de `__file__`).
- Tenga una función que procese el archivo y extraiga las coordenadas.
- Tenga una función `generar_mapa_<nombre>()` que cree el mapa con folium.
- Tenga un `layout = html.Div([...])` que muestre el mapa con `html.Iframe`.
- Centre el mapa en Gipuzkoa (lat=43.2, lon=-2.2, zoom=10).
- Use `Figure(width=1000, height=800)` como en el ejemplo.
- NO incluya rutas fijas, ni manipule carpetas ni `__file__`.
- Solo devuelva el código Python, sin explicaciones ni comentarios, ni con comillas de ''' python ni nada, la primera fila debe ser el primer import.

El código debe comenzar con las importaciones y ser listo para ejecutar en un entorno donde `archivo_excel` contiene la ruta al archivo.

Solo muestra los puntos cuya latitud esté entre 43.0 y 43.4 y longitud entre -2.49 y -1.7, es decir, filtra las filas con:

if not (43.0 <= lat <= 43.4 and -2.49 <= lon <= -1.7):
    continue

El archivo subido ya está guardado en disco y su ruta completa está disponible en la variable archivo_excel, que apunta a {tmp_path}. Según el tipo de archivo ({filename}), el código deberá usar pd.read_excel, pd.read_csv, etc.

En cuanto a qué meter dentro de los marcadores, deberás decidir tú, viendo la estructura del archivo, que data meter. 
"""

    try:
        chat = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return chat.choices[0].message.content
    except Exception as e:
        return f"# ERROR llamando a LLM: {str(e)}"

layout = html.Div([
    html.Div([
        html.H1("Generador inteligente de mapas", style={
            "textAlign": "center",
            "color": "black",
            "fontSize": "2rem",
            "marginBottom": "1px"
        }),
        html.P(
            "Esta herramienta utiliza inteligencia artificial para ayudarte a transformar tus propios datos geográficos en mapas interactivos sin necesidad de programar. "
            "Solo necesitas subir un archivo (CSV o Excel) que contenga información con coordenadas (latitud y longitud), y la IA generará automáticamente el código necesario para visualizarlo sobre un mapa. "
            "Una vez subido el archivo, el sistema mostrará un mapa interactivo con tus datos, además del código generado. Si el código tiene errores (por ejemplo, si el archivo está mal estructurado o faltan columnas), puedes escribir justo debajo en el cuadro \"Corregir código\", y la inteligencia artificial te devolverá una versión corregida. "
            "Además, puedes usar ese mismo cuadro para pedir modificaciones específicas en el mapa (cambio de colores/icono de los marcadores). En el caso que consideres que el mapa generado puede servir de gran información como para ponerlo en la página anterior, contacta con nosotros.",
            style={
                "textAlign": "center",
                "color": "black",
                "fontSize": "16px",
                "fontFamily": "'Segoe UI', sans-serif"
            }
        ),
    ], style={"padding": "5px", "borderBottom": "1px solid #ddd"}),


    html.Div([
        html.H3("Subir archivo de datos", style={"marginTop": "20px"}),
        dcc.Upload(
            id='upload-dataset',
            children=html.Div(['📂 Arrastra o selecciona un archivo CSV/Excel']),
            style={
                'width': '100%',
                'height': '100px',
                'lineHeight': '100px',
                'borderWidth': '2px',
                'borderStyle': 'dashed',
                'borderRadius': '10px',
                'textAlign': 'center',
                'margin': '10px 0',
                'backgroundColor': '#ffffff',
                'color': '#333',
                'fontWeight': 'bold'
            },
            multiple=False
        ),
        html.Div(id='mensaje-archivo', style={"marginBottom": "15px", "color": "green"}),
        
        html.Button("🤖 Generar mapa con IA", id="btn-generar-mapa", n_clicks=0, style={
            "backgroundColor": "#007bff",
            "color": "white",
            "padding": "10px 20px",
            "border": "none",
            "borderRadius": "5px",
            "fontSize": "1rem",
            "marginTop": "10px",
            "cursor": "pointer"
        }),

        html.Button("📩 Contactar", id="btn-contactar", n_clicks=0, style={
            "backgroundColor": "#ffc107",
            "color": "black",
            "padding": "10px 20px",
            "border": "none",
            "borderRadius": "5px",
            "fontSize": "1rem",
            "marginTop": "10px",
            "marginLeft": "10px",
            "cursor": "pointer"
        }, disabled=True),
        html.Div(
            id="formulario-contacto-modal",
            style={
                "display": "none",  
                "position": "fixed",
                "backgroundColor": "white",  
                "top": "40%",
                "left": "50%",
                "transform": "translate(-50%, -50%)",
                "zIndex": 9999,
                "padding": "35px",
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
                        html.P("Si considera que el mapa puede servir de información como para ponerlo en la página anterior, rellene el formulario y se enviará el mapa generado junto con el archivo CSV/Excel subido. ¡Lo valoraremos!", style={"color": "black", "textAlign": "center", "marginBottom": "25px", "fontWeight": "600", "fontSize": "0.8rem"}),
                        dcc.Input(id="input-nombre", type="text", placeholder="Nombre y Apellidos", style={
                            "width": "100%", "marginBottom": "15px", "padding": "8px", "fontSize": "0.9rem", "borderRadius": "6px", "border": "1px solid #ccc", "outline": "none",
                        }),
                        dcc.Input(id="input-telefono", type="text", placeholder="Teléfono", style={
                            "width": "100%", "marginBottom": "15px", "padding": "8px", "fontSize": "0.9rem", "borderRadius": "6px", "border": "1px solid #ccc", "outline": "none",
                        }),
                        dcc.Input(id="input-email", type="email", placeholder="Email", style={
                            "width": "100%", "marginBottom": "15px", "padding": "8px", "fontSize": "0.9rem", "borderRadius": "6px", "border": "1px solid #ccc", "outline": "none",
                        }),
                        dcc.Textarea(id="input-mensaje", placeholder="Mensaje: Explique lo que querría mostrar en el mapa y que información le gustaría mostrar dentro de los marcadores.", style={
                            "width": "100%", "height": "100px", "padding": "8px", "marginBottom": "20px", "fontSize": "0.9rem", "borderRadius": "6px", "border": "1px solid #ccc", "outline": "none", "resize": "vertical",
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

                        html.Div(id="mensaje-envio", style={"marginTop": "15px", "color": "green", "textAlign": "center", "fontWeight": "600"}),

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

        html.Button("Mostrar código Python generado", id="btn-toggle-codigo", n_clicks=0, style={
            "backgroundColor":  "#c9d4e0",
            "color": "white",
            "padding": "10px 20px",
            "border": "none",
            "borderRadius": "5px",
            "fontSize": "1rem",
            "marginTop": "10px",
            "marginLeft": "10px",
            "cursor": "pointer"
        }),
        dcc.Store(id="codigo-visible", data=False),
        html.Div(id="output-codigo-ia", style={
            "whiteSpace": "pre-wrap",
            "backgroundColor": "#f1f1f1",
            "padding": "15px",
            "marginTop": "10px",
            "border": "1px solid #ccc",
            "fontFamily": "Courier New, monospace",
            "borderRadius": "5px",
            "display": "none"
        }),
        html.Div(id="output-mapa", style={"marginTop": "30px"}),
    ], style={"padding": "20px"}),

    html.Div([
        html.H4("Chat para corregir código con IA", style={"marginTop": "30px", "color": "#333"}),
        dcc.Textarea(id="input-chat", style={
            "width": "100%",
            "height": 120,
            "padding": "10px",
            "borderRadius": "5px",
            "border": "1px solid #ccc",
            "fontFamily": "Courier New, monospace"
        }),
        html.Button("🛠️ Enviar corrección", id="btn-enviar-correccion", style={
            "backgroundColor": "#28a745",
             "color": "white",
            "padding": "10px 20px",
            "border": "none",
            "borderRadius": "5px",
            "fontSize": "1rem",
            "marginTop": "10px",
            "cursor": "pointer"
        }),
    ], style={"padding": "20px", "display": "none"}, id="chat-correction-div")
], style={"fontFamily": "Segoe UI, sans-serif", "backgroundColor": "#fafafa"})


# Memoria para contexto de chat
chat_history = []
def ejecutar_codigo_python(codigo_str):
    """
    Ejecuta el código python generado en memoria, captura 'layout' y 'mapa_html'.
    Devuelve el html del mapa o error si falla.
    """
    local_vars = {}
    try:
        exec(codigo_str, local_vars, local_vars)
        if 'mapa_html' in local_vars:
            return local_vars['mapa_html'], None
        elif 'layout' in local_vars:
            layout_obj = local_vars['layout']
            if hasattr(layout_obj, 'children'):
                for child in layout_obj.children:
                    if isinstance(child, html.Iframe):
                        return child.srcDoc, None
            return "<p>Mapa generado correctamente pero no encontrado en variable 'mapa_html'.</p>", None
        else:
            return "<p>No se encontró variable 'mapa_html' ni 'layout' con mapa.</p>", None
    except Exception as e:
        tb = traceback.format_exc()
        return None, f"Error ejecutando código:\n{tb}"

def register_callbacks(app):

    @app.callback(
        Output("mensaje-archivo", "children"),
        Input("upload-dataset", "contents"),
        State("upload-dataset", "filename")
    )
    
    def mostrar_mensaje_archivo(contents, filename):
        if contents and filename:
            return f"Archivo subido correctamente: {filename}"
        return ""

    @app.callback(
        Output("output-codigo-ia", "children"),
        Output("output-mapa", "children"),
        Output("chat-correction-div", "style"),
        Input("btn-generar-mapa", "n_clicks"),
        Input("btn-enviar-correccion", "n_clicks"),
        State("upload-dataset", "contents"),
        State("upload-dataset", "filename"),
        State("input-chat", "value"),
        prevent_initial_call=True
    )
    def manejar_interaccion(n_clicks_generar, n_clicks_correccion, contents, filename, texto_usuario):
        trigger_id = ctx.triggered_id

        if trigger_id == "btn-generar-mapa":
            if not contents or not filename:
                return "Por favor, sube un archivo válido antes de generar el código.", "", "", {"display": "none"}

            df_sample, error = parsear_contenido(contents, filename)
            if error:
                return error, "", "", {"display": "none"}

            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            suffix = os.path.splitext(filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(decoded)
                tmp_path = tmp.name

            codigo = llamar_a_deepseek(df_sample, filename, tmp_path)
            codigo = f"archivo_excel = r'''{tmp_path}'''\n" + codigo

            mapa_html, error_ejecucion = ejecutar_codigo_python(codigo)

            chat_history.clear()
            chat_history.append({"role": "system", "content": "Eres un asistente para corregir código Python generado para Dash. Recuerda que solo debes devolver el código Python, sin con comillas de ''' python ni nada, ya que debe ejecutarse bien y con esas comillas no funciona. La primera fila debe ser el primer import."})
            chat_history.append({"role": "user", "content": codigo})

            if error_ejecucion:
                chat_history.append({"role": "user", "content": f"Error al ejecutar: {error_ejecucion}"})
                return (
                    codigo + "\n\n# ERROR AL EJECUTAR:\n" + error_ejecucion,
                    html.Div("Error al ejecutar el código.", style={"color": "red"}),
                    {"display": "block"}
                )
            else:
                return (
                    codigo,
                    html.Iframe(srcDoc=mapa_html, width="100%", height="800"),
                    {"display": "block"}
                )

        elif trigger_id == "btn-enviar-correccion":
            if not texto_usuario or len(chat_history) == 0:
                return dash.no_update, dash.no_update, "Escribe una corrección o pregunta.", dash.no_update

            chat_history.append({"role": "user", "content": texto_usuario})

            try:
                respuesta = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=chat_history,
                    temperature=0.2
                )
                respuesta_texto = respuesta.choices[0].message.content
                chat_history.append({"role": "assistant", "content": respuesta_texto})

                mapa_html, error_ejecucion = ejecutar_codigo_python(respuesta_texto)

                if error_ejecucion:
                    return (
                        respuesta_texto + "\n\n# ERROR AL EJECUTAR:\n" + error_ejecucion,
                        html.Div("Error al ejecutar el código corregido.", style={"color": "red"}),
                        {"display": "block"}
                    )
                else:
                    return (
                        respuesta_texto,
                        html.Iframe(srcDoc=mapa_html, width="100%", height="800"),
                        {"display": "block"}
                    )

            except Exception as e:
                return dash.no_update, dash.no_update, f"Error llamando a la IA: {str(e)}", dash.no_update

        # fallback
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    @app.callback(
        Output("output-codigo-ia", "style"),
        Output("codigo-visible", "data"),
        Input("btn-toggle-codigo", "n_clicks"),
        State("codigo-visible", "data"),
        prevent_initial_call=True
    )
    def toggle_codigo(n_clicks, visible):
        nuevo_estado = not visible
        estilo = {
            "whiteSpace": "pre-wrap",
            "backgroundColor": "#f1f1f1",
            "padding": "15px",
            "marginTop": "10px",
            "border": "1px solid #ccc",
            "fontFamily": "Courier New, monospace",
            "borderRadius": "5px",
            "display": "block" if nuevo_estado else "none"
        }
        return estilo, nuevo_estado
    
    @app.callback(
        Output("formulario-contacto", "style"),
        Output("btn-contactar", "disabled"),
        Input("output-mapa", "children"),
        prevent_initial_call=True
    )
    def habilitar_contactar(mapa):
        if mapa:
            return {"display": "block", "marginTop": "20px"}, False
        return {"display": "none"}, True
    
    @app.callback(
    Output("mensaje-envio", "children"),
    Input("btn-enviar-formulario", "n_clicks"),
    State("input-nombre", "value"),
    State("input-telefono", "value"),
    State("input-email", "value"),
    State("input-mensaje", "value"),
    State("output-codigo-ia", "children"),
    prevent_initial_call=True
    )
    def enviar_formulario(n_clicks, nombre, telefono, email, mensaje, codigo):
        try:
            if not all([nombre, telefono, email, mensaje, codigo]):
                return "Por favor completa todos los campos."

            msg = EmailMessage()
            msg["Subject"] = "Nuevo formulario de contacto - Mapa Dash"
            msg["From"] = email
            msg["To"] = "mzuazolaarr@alumni.unav.es"
            cuerpo = f"""
            Nombre y Apellidos: {nombre}
            Teléfono: {telefono}
            Email: {email}
            Mensaje: {mensaje}
            """
            msg.set_content(cuerpo)

            # Adjuntar el código Python generado
            msg.add_attachment(codigo.encode("utf-8"), maintype='application', subtype='octet-stream', filename="codigo_generado.py")

            # Enviar el correo (ajusta según tu servidor SMTP)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login('appdatosmovilidad@gmail.com', 'wovz ejwt xkfd amzg')
                smtp.send_message(msg)

            return "Formulario enviado correctamente. ¡Gracias por tu interés!"
        except Exception as e:
            return f"Error al enviar el formulario: {str(e)}"
        
    @app.callback(
    Output("formulario-contacto-modal", "style"),
    Input("btn-contactar", "n_clicks"),
    Input("btn-cerrar-modal", "n_clicks"),
    State("formulario-contacto-modal", "style"),
    prevent_initial_call=True
)
    def toggle_modal(n_clicks_open, n_clicks_close, current_style):
        trigger = ctx.triggered_id
        if trigger == "btn-contactar":
            return {**current_style, "display": "flex"}
        elif trigger == "btn-cerrar-modal":
            return {**current_style, "display": "none"}
        return current_style

def parsear_contenido(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(decoded.decode('iso-8859-1')), sep='\t')
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(decoded))
            lat_col, lon_col = detectar_columnas_lat_lon(df)
            if lat_col:
                df[lat_col] = df[lat_col].astype(str).str.replace(',', '.').astype(float)
            if lon_col:
                df[lon_col] = df[lon_col].astype(str).str.replace(',', '.').astype(float)
        else:
            return None, "Formato de archivo no soportado."
        return df.head(10), None
    except Exception as e:
        return None, f"Error leyendo archivo: {str(e)}"
    

