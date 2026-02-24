"""Configuration constants for tidal variance analysis."""

from pathlib import Path

NOAA_API_URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"

STATION_ID = "9414131"
DAY_START_HOUR = 10
DAY_END_HOUR = 16
TIDEPOOL_TIDE = 0.1

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_RAW_DIR = PROJECT_ROOT / "data/raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data/processed"
OUT_PLOTS_DIR = PROJECT_ROOT / "out/plots"
