import dash
from dash import html, dcc, dash_table, Input, Output, State
import pandas as pd
import psycopg2
import datetime

# Parámetros de conexión fijos
DB_HOST = '34.245.188.222'
DB_PORT = '5432'
DB_NAME = 'gll_data'


def get_data(start_date, end_date, db_user, db_pass):
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=db_user,
        password=db_pass
    )

    query = f"""
    WITH intervalos AS ( 
      SELECT generate_series(
        '{start_date} 00:00:00'::timestamp,
        '{end_date} 23:55:00'::timestamp,
        interval '5 minutes'
      ) AS intervalo_5min
    ),
    rsus AS (
      SELECT DISTINCT rsu FROM public.data_bluetooth
    ),
    conteos AS (
      SELECT 
        rsu,
        date_trunc('hour', to_timestamp(timestamp)) + 
          interval '5 minutes' * floor(extract(minute from to_timestamp(timestamp)) / 5) AS intervalo_5min,
        COUNT(*) AS vehiculos_contados
      FROM 
        public.data_bluetooth
      WHERE 
        class_of_device::text LIKE '%0408'
        AND to_timestamp(timestamp) BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
      GROUP BY 
        rsu, intervalo_5min
    )
    SELECT 
      r.rsu,
      i.intervalo_5min,
      COALESCE(c.vehiculos_contados, 0) AS vehiculos_contados
    FROM 
      rsus r
    CROSS JOIN 
      intervalos i
    LEFT JOIN 
      conteos c ON c.rsu = r.rsu AND c.intervalo_5min = i.intervalo_5min
    ORDER BY 
      r.rsu, i.intervalo_5min;
    """

    df = pd.read_sql(query, conn)
    conn.close()
    return df


layout = html.Div([
    html.Div([
        html.H1("Descarga y Visualización de Datos RSU", style={
            "textAlign": "center",
            "color": "black",
            "fontSize": "2rem",
            "marginBottom": "1px"
        }),
        html.P("Este módulo permite visualizar y descargar datos de conteos Bluetooth desde RSU, por intervalo de 5 minutos.", style={
            "textAlign": "center",
            "fontSize": "16px"
        })
    ], style={"padding": "5px", "borderBottom": "1px solid #ddd"}),

    html.Div([
        html.Div([
            html.Label("Usuario:", style={"marginRight": "10px"}),
            dcc.Input(id='db-usuario', type='text', value='', placeholder='Introduce el usuario'),

            html.Label("Contraseña:", style={"marginLeft": "20px", "marginRight": "10px"}),
            dcc.Input(id='db-contrasena', type='password', value='', placeholder='Introduce la contraseña'),
        ], style={"textAlign": "center", "marginBottom": "20px"}),

        html.Div([
            html.Label("Selecciona el rango de fechas:", style={"fontWeight": "bold", "marginRight": "10px"}),
            dcc.DatePickerRange(
                id='fecha-rango-rsu',
                display_format='YYYY-MM-DD',
                start_date=datetime.date(2025, 4, 10),
                end_date=datetime.date(2025, 4, 20),
                style={
                    "border": "1px solid #ccc",
                    "borderRadius": "6px",
                    "padding": "8px",
                    "boxShadow": "0 1px 4px rgba(0,0,0,0.1)",
                    "fontSize": "14px"
                }
            )
        ], style={"marginBottom": "20px", "textAlign": "center"}),

        html.Div([
            html.Button("Mostrar datos", id="btn-mostrar-rsu", n_clicks=0, style={
                "backgroundColor": "blue",
                "color": "white",
                "border": "none",
                "borderRadius": "6px",
                "padding": "5px 10px",
                "fontSize": "14px",
                "cursor": "pointer",
                "marginRight": "10px",
                "boxShadow": "0 2px 6px rgba(0, 0, 0, 0.15)"
            }),
            html.Button("Descargar CSV", id="btn-descargar-rsu", n_clicks=0, style={
                "backgroundColor": "green",
                "color": "white",
                "border": "none",
                "borderRadius": "6px",
                "padding": "5px 10px",
                "fontSize": "14px",
                "cursor": "pointer",
                "boxShadow": "0 2px 6px rgba(0, 0, 0, 0.15)"
            })
        ], style={"textAlign": "center", "marginBottom": "20px"}),

        html.Br(),
        html.Div(id="tabla-vista-previa-rsu"),
        dcc.Download(id="descarga-csv-rsu")
    ], style={"padding": "20px", "maxWidth": "900px", "margin": "0 auto"})
])


def register_callbacks(app):
    @app.callback(
        Output("tabla-vista-previa-rsu", "children"),
        Input("btn-mostrar-rsu", "n_clicks"),
        State("fecha-rango-rsu", "start_date"),
        State("fecha-rango-rsu", "end_date"),
        State("db-usuario", "value"),
        State("db-contrasena", "value")
    )
    def mostrar_datos(n, start_date, end_date, db_user, db_pass):
        if n == 0 or not start_date or not end_date or not db_user or not db_pass:
            return dash.no_update
        try:
            df = get_data(start_date, end_date, db_user, db_pass)
            return dash_table.DataTable(
                data=df.head(10).to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
                page_size=10,
                style_table={"overflowX": "auto"}
            )
        except Exception as e:
            return html.Div(f"Error al conectar a la base de datos: {str(e)}", style={"color": "red"})

    @app.callback(
        Output("descarga-csv-rsu", "data"),
        Input("btn-descargar-rsu", "n_clicks"),
        State("fecha-rango-rsu", "start_date"),
        State("fecha-rango-rsu", "end_date"),
        State("db-usuario", "value"),
        State("db-contrasena", "value"),
        prevent_initial_call=True
    )
    def descargar_csv(n, start_date, end_date, db_user, db_pass):
        try:
            df = get_data(start_date, end_date, db_user, db_pass)
            return dcc.send_data_frame(df.to_csv, f"datos_rsu_{start_date}_a_{end_date}.csv", index=False)
        except Exception as e:
            return dash.no_update
