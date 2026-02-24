"""Configuration constants for tidal variance analysis."""

from pathlib import Path

NOAA_API_URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"

STATION_ID = "9414131"
DAY_START_HOUR = 10
DAY_END_HOUR = 16
TIDEPOOL_TIDE = 0.1

DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
OUT_PLOTS_DIR = Path("out/plots")
