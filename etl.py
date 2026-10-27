"""Extract, clean, and store World Bank indicators in a local SQLite database."""

from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://api.worldbank.org/v2"
DATABASE_PATH = Path(__file__).parent / "data" / "economic_indicators.sqlite"
INDICATORS = {
    "NY.GDP.MKTP.CD": "PIB (US$ actuales)",
    "NY.GDP.MKTP.KD.ZG": "Crecimiento del PIB (%)",
    "FP.CPI.TOTL.ZG": "Inflación (%)",
    "SL.UEM.TOTL.ZS": "Desempleo (%)",
    "SP.POP.TOTL": "Población",
}
DEFAULT_COUNTRIES = ["USA", "MEX", "COL", "ESP", "BRA", "CHL"]
TABLE_COLUMNS = [
    "country_code",
    "country_name",
    "indicator_code",
    "indicator_name",
    "year",
    "value",
    "fetched_at",
]


def fetch_indicator(
    indicator_code: str,
    countries: list[str],
    start_year: int,
    end_year: int,
) -> list[dict]:
    country_path = ";".join(country.upper() for country in countries)
    url = f"{API_URL}/country/{country_path}/indicator/{indicator_code}"
    response = requests.get(
        url,
        params={
            "format": "json",
            "per_page": 2000,
            "date": f"{start_year}:{end_year}",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError(f"Respuesta inesperada para el indicador {indicator_code}")
    return payload[1] or []


def extract_and_clean(
    countries: list[str], start_year: int = 2015, end_year: int | None = None
) -> pd.DataFrame:
    end_year = end_year or datetime.now(timezone.utc).year
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []

    for code, name in INDICATORS.items():
        for item in fetch_indicator(code, countries, start_year, end_year):
            country = item.get("country") or {}
            rows.append(
                {
                    "country_code": item.get("countryiso3code"),
                    "country_name": country.get("value"),
                    "indicator_code": code,
                    "indicator_name": name,
                    "year": item.get("date"),
                    "value": item.get("value"),
                    "fetched_at": fetched_at,
                }
            )

    frame = pd.DataFrame(rows, columns=TABLE_COLUMNS)
    if frame.empty:
        return frame

    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame.dropna(
        subset=["country_code", "country_name", "year", "value"]
    )
    frame["year"] = frame["year"].astype(int)
    frame["country_code"] = frame["country_code"].str.upper().str.strip()
    frame = frame[frame["country_code"].isin(country.upper() for country in countries)]
    return frame.drop_duplicates(
        subset=["country_code", "indicator_code", "year"], keep="last"
    ).reset_index(drop=True)


def load_to_sqlite(frame: pd.DataFrame, database_path: Path = DATABASE_PATH) -> int:
    if frame.empty:
        return 0

    database_path.parent.mkdir(parents=True, exist_ok=True)
    placeholders = ", ".join("?" for _ in TABLE_COLUMNS)
    columns = ", ".join(TABLE_COLUMNS)
    query = (
        f"INSERT OR REPLACE INTO economic_indicators ({columns}) "
        f"VALUES ({placeholders})"
    )
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            f"""CREATE TABLE IF NOT EXISTS economic_indicators (
                country_code TEXT NOT NULL,
                country_name TEXT NOT NULL,
                indicator_code TEXT NOT NULL,
                indicator_name TEXT NOT NULL,
                year INTEGER NOT NULL,
                value REAL NOT NULL,
                fetched_at TEXT NOT NULL,
                PRIMARY KEY (country_code, indicator_code, year)
            )"""
        )
        connection.executemany(query, frame[TABLE_COLUMNS].itertuples(index=False, name=None))
    return len(frame)


def run_pipeline(
    countries: list[str], start_year: int = 2015, end_year: int | None = None
) -> int:
    frame = extract_and_clean(countries, start_year, end_year)
    return load_to_sqlite(frame)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--countries",
        nargs="+",
        default=DEFAULT_COUNTRIES,
        help="Códigos ISO-3 separados por espacios (por defecto: USA MEX COL ESP BRA CHL)",
    )
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=None)
    arguments = parser.parse_args()
    count = run_pipeline(arguments.countries, arguments.start_year, arguments.end_year)
    print(f"ETL completado: {count} registros guardados en {DATABASE_PATH}")


if __name__ == "__main__":
    main()