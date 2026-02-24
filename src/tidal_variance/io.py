"""I/O helpers for tidal variance analysis."""

from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from .config import DATA_PROCESSED_DIR, DATA_RAW_DIR, NOAA_API_URL, OUT_PLOTS_DIR

try:
    from api_token import API_TOKEN
except (ImportError, AttributeError):
    API_TOKEN = None
    print("Warning: API_TOKEN not found. 'water_level' data will not be available.")


def ensure_project_directories():
    """Ensure project data/output directories exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def ensure_api_token_file():
    """Create a token template file if API token is not configured."""
    if API_TOKEN is not None:
        return

    token_file = Path("api_token.py")
    if not token_file.exists():
        token_file.write_text(
            "# api_token.py\n"
            'API_TOKEN = "YOUR_NOAA_API_TOKEN"  # Replace with your actual token\n',
            encoding="utf-8",
        )
        print("Created 'api_token.py'. Please add your API_TOKEN to this file.")
        return

    print("'api_token.py' exists but API_TOKEN is not defined. Please add your API_TOKEN.")


def fetch_tidal_data(station_id, start_date, end_date, product="predictions"):
    """Fetch tidal data from NOAA API."""
    params = {
        "product": product,
        "application": "web_services",
        "begin_date": start_date.strftime("%Y%m%d"),
        "end_date": end_date.strftime("%Y%m%d"),
        "datum": "MLLW",
        "station": station_id,
        "time_zone": "lst_ldt",
        "units": "english",
        "interval": "hilo",
        "format": "json",
    }

    if product == "water_level":
        if not API_TOKEN:
            print("Error: API_TOKEN is not available. Cannot fetch 'water_level' data.")
            return pd.DataFrame()
        if API_TOKEN == "YOUR_NOAA_API_TOKEN":
            print(
                "Warning: API_TOKEN not defined. Should be set in api_token.py. "
                "Cannot fetch 'water_level' data."
            )
            return pd.DataFrame()
        params["token"] = API_TOKEN

    try:
        response = requests.get(NOAA_API_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as exc:
        print(f"HTTP Request failed: {exc}")
        return pd.DataFrame()
    except ValueError as exc:
        print(f"JSON decoding failed: {exc}")
        return pd.DataFrame()

    key = "water_level" if product == "water_level" else "predictions"
    if key not in data:
        raise ValueError(f"Unexpected response format: {data}")

    df = pd.DataFrame(data[key])
    df["t"] = pd.to_datetime(df["t"])
    df["v"] = pd.to_numeric(df["v"])
    return df


def build_period_suffix(start_year, end_year):
    """Build a standard year suffix for output filenames."""
    return f"{start_year}_{end_year}"


def append_period_to_filename(filename, period_suffix):
    """Append the period suffix before the file extension."""
    path = Path(filename)
    return path.with_name(f"{path.stem}_{period_suffix}{path.suffix}")


def export_to_csv(df, filename):
    """Export DataFrame to a CSV file, rotating any existing output file."""
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rotated_path = output_path.with_name(
            f"{output_path.stem}.bak_{timestamp}{output_path.suffix}"
        )
        print(
            f"Warning: {output_path} already exists. "
            f"Renaming existing file to {rotated_path}."
        )
        output_path.rename(rotated_path)

    df.to_csv(output_path, index=False)
    print(f"Data exported to {output_path}")


def resolve_input_path(path_str, base_dir=None):
    """Resolve an input path robustly for CLI and debugger launches."""
    candidate = Path(path_str).expanduser()
    if candidate.exists():
        return candidate.resolve()

    base_dir = Path(base_dir) if base_dir is not None else Path(__file__).resolve().parent
    base_dir_candidate = (base_dir / candidate).resolve()
    if base_dir_candidate.exists():
        return base_dir_candidate

    return None
