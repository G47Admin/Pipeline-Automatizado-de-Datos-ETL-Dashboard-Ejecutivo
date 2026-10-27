from __future__ import annotations

import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

from etl import DATABASE_PATH, DEFAULT_COUNTRIES, INDICATORS, run_pipeline

st.set_page_config(
    page_title="Pulso | Inteligencia económica",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,500;6..72,600&display=swap');
    :root {
        --ink: #17231f;
        --muted: #64736c;
        --line: #dce5df;
        --paper: #f5f7f3;
        --green: #1d7655;
        --lime: #d9ef72;
        --orange: #e8794f;
    }
    html, body, [class*="css"], .stApp { font-family: 'DM Sans', sans-serif; color: var(--ink); }
    .stApp { background: var(--paper); }
    [data-testid="stSidebar"] { background: #eaf0e9; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] h1 { font-family: 'Newsreader', serif; font-size: 30px; }
    .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 3rem; }
    .eyebrow { color: var(--green); font: 500 11px 'DM Mono', monospace; letter-spacing: 1.4px; text-transform: uppercase; }
    .hero-title { font: 500 clamp(38px, 5vw, 64px)/1.02 'Newsreader', serif; margin: 8px 0 10px; }
    .hero-sub { color: var(--muted); font-size: 15px; margin: 0 0 24px; }
    .section-title { font: 600 22px 'Newsreader', serif; margin: 26px 0 4px; }
    .section-note { color: var(--muted); font-size: 12px; margin: 0 0 12px; }
    .metric-box { background: #fff; border: 1px solid var(--line); border-top: 3px solid var(--green); padding: 16px 18px; min-height: 110px; }
    .metric-label { color: var(--muted); font: 500 11px 'DM Mono', monospace; text-transform: uppercase; letter-spacing: .5px; }
    .metric-value { font: 600 27px 'Newsreader', serif; margin-top: 8px; }
    .metric-caption { color: var(--muted); font-size: 11px; margin-top: 2px; }
    .source-line { color: var(--muted); font: 11px 'DM Mono', monospace; border-top: 1px solid var(--line); margin-top: 26px; padding-top: 12px; }
    div[data-testid="stMetric"] { background: white; border: 1px solid var(--line); border-top: 3px solid var(--green); padding: 15px 17px; }
    div[data-testid="stMetricLabel"] { color: var(--muted); font: 500 11px 'DM Mono', monospace; text-transform: uppercase; }
    div[data-testid="stMetricValue"] { font: 600 26px 'Newsreader', serif; }
    div.stButton > button { border-radius: 3px; border: 0; background: var(--green); color: white; font-weight: 600; }
    div.stButton > button:hover { background: #155b40; color: white; border: 0; }
    [data-testid="stDataFrame"] { border: 1px solid var(--line); }
    @media (max-width: 700px) { .block-container { padding: 1.2rem 1rem 2rem; } .hero-sub { font-size: 14px; } }
    </style>
    """,
    unsafe_allow_html=True,
)

COUNTRIES = {
    "USA": "Estados Unidos",
    "MEX": "México",
    "COL": "Colombia",
    "ESP": "España",
    "BRA": "Brasil",
    "CHL": "Chile",
    "ARG": "Argentina",
    "PER": "Perú",
    "CAN": "Canadá",
    "DEU": "Alemania",
    "FRA": "Francia",
    "JPN": "Japón",
}
COLORS = ["#1d7655", "#e8794f", "#7793c2", "#b0a238", "#a26889", "#58a7a0"]


def read_data() -> pd.DataFrame:
    if not DATABASE_PATH.exists():
        return pd.DataFrame()
    with sqlite3.connect(DATABASE_PATH) as connection:
        return pd.read_sql_query(
            "SELECT * FROM economic_indicators ORDER BY year", connection
        )


def format_value(indicator_code: str, value: float) -> str:
    if indicator_code == "NY.GDP.MKTP.CD":
        return f"US$ {value / 1e12:,.2f} billones"
    if indicator_code == "SP.POP.TOTL":
        return f"{value / 1e6:,.1f} M"
    return f"{value:,.1f}%"


with st.sidebar:
    st.markdown("<p class='eyebrow'>DATA INTELLIGENCE / 01</p>", unsafe_allow_html=True)
    st.title("Pulso")
    st.caption("Radar de indicadores económicos")
    st.divider()
    selected_countries = st.multiselect(
        "Mercados",
        options=list(COUNTRIES),
        default=DEFAULT_COUNTRIES,
        format_func=lambda code: f"{COUNTRIES[code]} · {code}",
    )
    start_year = st.slider("Desde", min_value=2000, max_value=2025, value=2015)
    st.caption("Cinco indicadores · actualización desde Banco Mundial")
    refresh = st.button("↻  Sincronizar datos", use_container_width=True)

if refresh:
    if not selected_countries:
        st.sidebar.error("Selecciona al menos un mercado.")
    else:
        with st.spinner("Consultando API y actualizando la base local…"):
            try:
                count = run_pipeline(selected_countries, start_year)
                st.success(f"Sincronización lista: {count:,} registros procesados.")
            except (OSError, ValueError, sqlite3.Error) as error:
                st.error(f"No se pudo completar la sincronización: {error}")
            except Exception as error:
                st.error(f"Error al consultar el Banco Mundial: {error}")

if not selected_countries:
    st.warning("Selecciona al menos un mercado en la barra lateral.")
    st.stop()

data = read_data()
if not data.empty:
    data = data[
        data["country_code"].isin(selected_countries) & (data["year"] >= start_year)
    ]

st.markdown("<p class='eyebrow'>PANEL EJECUTIVO &nbsp; / &nbsp; ECONOMÍA GLOBAL</p>", unsafe_allow_html=True)
st.markdown("<h1 class='hero-title'>El contexto detrás<br>de cada decisión.</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='hero-sub'>Una lectura comparativa de crecimiento, precios y empleo en tus mercados.</p>",
    unsafe_allow_html=True,
)

if data.empty:
    st.info("Aún no hay datos locales. Pulsa «Sincronizar datos» para ejecutar el ETL y cargar la primera serie.")
    st.stop()

latest = data.sort_values("year").groupby(
    ["country_code", "indicator_code"], as_index=False
).tail(1)
growth = latest[latest["indicator_code"] == "NY.GDP.MKTP.KD.ZG"]["value"]
inflation = latest[latest["indicator_code"] == "FP.CPI.TOTL.ZG"]["value"]
unemployment = latest[latest["indicator_code"] == "SL.UEM.TOTL.ZS"]["value"]
latest_year = int(latest["year"].max()) if not latest.empty else "—"
updated_at = data["fetched_at"].max()

metric_columns = st.columns(4)
metrics = [
    ("Mercados activos", f"{data['country_code'].nunique():02d}", "Países en comparación"),
    ("Crecimiento mediano", f"{growth.median():.1f}%" if not growth.empty else "s/d", f"Último dato · {latest_year}"),
    ("Inflación mediana", f"{inflation.median():.1f}%" if not inflation.empty else "s/d", f"Último dato · {latest_year}"),
    ("Desempleo mediano", f"{unemployment.median():.1f}%" if not unemployment.empty else "s/d", f"Último dato · {latest_year}"),
]
for column, (label, value, caption) in zip(metric_columns, metrics):
    with column:
        st.metric(label, value, help=caption)

st.markdown("<h2 class='section-title'>Trayectoria de crecimiento</h2>", unsafe_allow_html=True)
st.markdown("<p class='section-note'>Variación anual del PIB real · porcentaje</p>", unsafe_allow_html=True)
growth_data = data[data["indicator_code"] == "NY.GDP.MKTP.KD.ZG"].copy()
if not growth_data.empty:
    growth_data["País"] = growth_data["country_code"].map(COUNTRIES).fillna(growth_data["country_name"])
    chart = px.line(
        growth_data,
        x="year",
        y="value",
        color="País",
        markers=True,
        color_discrete_sequence=COLORS,
        labels={"year": "Año", "value": "Crecimiento (%)", "País": "Mercado"},
    )
    chart.update_traces(line={"width": 2.5}, marker={"size": 5})
    chart.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "DM Sans", "color": "#64736c", "size": 11},
        margin={"l": 8, "r": 12, "t": 16, "b": 8},
        legend={"orientation": "h", "y": 1.12, "x": 0},
        xaxis={"dtick": 2, "gridcolor": "#e3e9e3", "zeroline": False},
        yaxis={"ticksuffix": "%", "gridcolor": "#e3e9e3", "zerolinecolor": "#aab7ad"},
        hovermode="x unified",
    )
    st.plotly_chart(chart, use_container_width=True)
else:
    st.warning("No hay datos de crecimiento para el periodo seleccionado.")

left, right = st.columns([1.1, 0.9], gap="large")
with left:
    st.markdown("<h2 class='section-title'>Presión de precios</h2>", unsafe_allow_html=True)
    st.markdown("<p class='section-note'>Inflación anual · último dato disponible por mercado</p>", unsafe_allow_html=True)
    latest_inflation = latest[latest["indicator_code"] == "FP.CPI.TOTL.ZG"].copy()
    if not latest_inflation.empty:
        latest_inflation["País"] = latest_inflation["country_code"].map(COUNTRIES).fillna(latest_inflation["country_name"])
        bar = px.bar(
            latest_inflation.sort_values("value"),
            x="value", y="País", orientation="h", text_auto=".1f",
            color="value", color_continuous_scale=["#d9ef72", "#1d7655", "#e8794f"],
            labels={"value": "Inflación (%)", "País": ""},
        )
        bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font={"family": "DM Sans", "color": "#64736c", "size": 11},
            margin={"l": 0, "r": 12, "t": 8, "b": 8},
            coloraxis_showscale=False, xaxis={"ticksuffix": "%", "gridcolor": "#e3e9e3"},
        )
        st.plotly_chart(bar, use_container_width=True)
    else:
        st.caption("Sin datos disponibles.")

with right:
    st.markdown("<h2 class='section-title'>Pulso del empleo</h2>", unsafe_allow_html=True)
    st.markdown("<p class='section-note'>Desempleo · último dato disponible</p>", unsafe_allow_html=True)
    latest_unemployment = latest[latest["indicator_code"] == "SL.UEM.TOTL.ZS"].copy()
    if not latest_unemployment.empty:
        latest_unemployment["País"] = latest_unemployment["country_code"].map(COUNTRIES).fillna(latest_unemployment["country_name"])
        employment = px.bar(
            latest_unemployment.sort_values("value"),
            x="value", y="País", orientation="h", text_auto=".1f",
            color_discrete_sequence=["#e8794f"],
            labels={"value": "Desempleo (%)", "País": ""},
        )
        employment.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font={"family": "DM Sans", "color": "#64736c", "size": 11},
            margin={"l": 0, "r": 12, "t": 8, "b": 8},
            xaxis={"ticksuffix": "%", "gridcolor": "#e3e9e3"},
        )
        st.plotly_chart(employment, use_container_width=True)
    else:
        st.caption("Sin datos disponibles.")

st.markdown("<h2 class='section-title'>Ficha de mercados</h2>", unsafe_allow_html=True)
st.markdown("<p class='section-note'>Último valor publicado por indicador · el año puede variar según la fuente.</p>", unsafe_allow_html=True)
latest_table = latest.copy()
latest_table["País"] = latest_table["country_code"].map(COUNTRIES).fillna(latest_table["country_name"])
latest_table["Valor"] = latest_table.apply(
    lambda row: f"{format_value(row['indicator_code'], row['value'])} · {int(row['year'])}",
    axis=1,
)
table = latest_table.pivot_table(
    index=["country_code", "País"], columns="indicator_name", values="Valor", aggfunc="first"
).reset_index().rename(columns={"country_code": "ISO", "País": "Mercado"})
ordered_columns = ["Mercado", "ISO"] + [name for name in INDICATORS.values() if name in table.columns]
st.dataframe(table[ordered_columns], hide_index=True, use_container_width=True)

st.markdown(
    f"<p class='source-line'>FUENTE: BANCO MUNDIAL · API V2 &nbsp;&nbsp;|&nbsp;&nbsp; ÚLTIMA SINCRONIZACIÓN: {updated_at} UTC &nbsp;&nbsp;|&nbsp;&nbsp; ALMACÉN: SQLITE LOCAL</p>",
    unsafe_allow_html=True,
)