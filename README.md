# Pulso: ETL y dashboard ejecutivo

Dashboard en español para comparar crecimiento, inflación, desempleo, PIB y población. El ETL consulta la API pública del Banco Mundial, normaliza valores y años, elimina registros incompletos/duplicados y guarda los resultados en SQLite.

## Requisitos

- Python 3.10 o posterior
- Conexión a internet para sincronizar la API del Banco Mundial
- No se necesita API key ni una cuenta externa

## Puesta en marcha

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Al abrir el dashboard, pulsa **Sincronizar datos**. La selección de mercados y el año de inicio se controlan desde la barra lateral. La base local se crea en `data/economic_indicators.sqlite`.

También puedes ejecutar el ETL sin abrir el dashboard:

```powershell
python etl.py --countries USA MEX COL ESP BRA CHL --start-year 2015
```

## Flujo

1. **Extracción:** cinco indicadores de la API v2 del Banco Mundial, agrupando países para reducir llamadas.
2. **Transformación:** tipado numérico, normalización ISO, eliminación de valores nulos y duplicados.
3. **Carga:** inserción idempotente en SQLite, con clave única por país, indicador y año.
4. **Visualización:** evolución del PIB real y comparativas de inflación, desempleo y otros indicadores.

Los datos están sujetos a la disponibilidad y revisiones de la fuente. El año más reciente varía según país e indicador.