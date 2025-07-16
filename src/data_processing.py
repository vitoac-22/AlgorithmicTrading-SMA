# src/data_processing.py
import os
import pandas as pd
import yfinance as yf
from alpaca_trade_api import REST
from dotenv import load_dotenv
from config import SYMBOL, START_DATE, END_DATE, INTERVAL, DATA_PATH

load_dotenv()  # Carga variables de .env


def download_yfinance_data(symbol, start, end, interval):
    """Descarga datos históricos de Yahoo Finance"""
    df = yf.download(symbol, start=start, end=end, interval=interval)
    return df


def download_alpaca_data(symbol, start, end, timeframe="1Day"):
    """Descarga datos históricos de Alpaca"""
    api = REST(
        os.getenv("ALPACA_API_KEY"),
        os.getenv("ALPACA_SECRET_KEY"),
        base_url=os.getenv("ALPACA_BASE_URL"),
    )

    # Convertir fechas a formato ISO
    start_iso = pd.Timestamp(start).isoformat() + "Z"
    end_iso = pd.Timestamp(end).isoformat() + "Z"

    # Obtener datos
    bars = api.get_bars(symbol, timeframe, start=start_iso, end=end_iso).df

    return bars


def preprocess_data(df):
    """Limpieza y preprocesamiento de datos"""
    # Manejar valores faltantes
    df = df.ffill().bfill().dropna()

    # Normalizar nombres de columnas
    df = df.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )

    # Filtrar datos fuera de horario bursátil
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.between_time("09:30", "16:00")

    return df


def save_data(df, filename, folder="raw"):
    """Guarda datos en CSV"""
    path = f"{DATA_PATH}{folder}/"
    os.makedirs(path, exist_ok=True)
    filepath = f"{path}{filename}.csv"
    df.to_csv(filepath)
    return filepath


if __name__ == "__main__":
    try:
        # Intentar con Alpaca primero
        print("Intentando descargar datos de Alpaca...")
        raw_data = download_alpaca_data(SYMBOL, START_DATE, END_DATE)
        source = "alpaca"
    except Exception as e:
        print(f"Error con Alpaca ({e}), usando Yahoo Finance...")
        raw_data = download_yfinance_data(SYMBOL, START_DATE, END_DATE, INTERVAL)
        source = "yfinance"

    # Guardar datos crudos
    raw_path = save_data(raw_data, f"{SYMBOL}_raw_{source}")
    print(f"Datos crudos guardados en: {raw_path}")

    # Preprocesar
    processed_data = preprocess_data(raw_data)

    # Guardar datos procesados
    processed_path = save_data(processed_data, f"{SYMBOL}_processed", "processed")
    print(f"Datos procesados guardados en: {processed_path}")
