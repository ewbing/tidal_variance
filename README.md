# Tidal Variance

Analyze NOAA tide predictions to identify seasonal patterns for good tide pooling
Focus on low-tide patterns during the day, generates monthly summaries, and export charts/CSVs for exploration

## Features

- Load tide data from `CSV` files (default)
- Fetch tide data from NOAA API (`predictions` or `water_level` based on token status)
- Identify lower-low tides from low-tide points
- Compute monthly aggregates, including daytime and threshold-based metrics
- Export processed datasets to `data/processed/`
- Generate plots in `out/plots/`

## Project Structure

```text
tidal_variance/
├── data/
│   ├── raw/
│   └── processed/
├── out/
│   └── plots/
├── src/tidal_variance/
│   ├── analysis.py
│   ├── cli.py
│   ├── config.py
│   ├── io.py
│   └── plotting.py
├── tests/
├── monthly_tidal_variance.py
└── requirements.txt
```

## Requirements

- Python 3.10+ (recommended)
- `pip`

## Installation

```bash
git clone <your-repo-url>
cd tidal_variance
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Run from CSV (default)

```bash
python monthly_tidal_variance.py \
  --source csv \
  --csv_path data/raw/raw_tide_data.csv
```

### Run from NOAA API

```bash
python monthly_tidal_variance.py --source api
```

### NOAA token setup (optional, recommended)

The generic `api_token.py` file contains:

```python
API_TOKEN = "YOUR_NOAA_API_TOKEN"  # Replace with your actual token
```

Replace the placeholder with your NOAA token to enable higher-throughput NOAA requests and to fetch actual tide data (`water_level`) instead of only predictions.

Do not check real tokens into git. `api_token.py` is already listed in `.gitignore`.

Notes:

- Source CSV must include at least `t` (timestamp), `v` (tide height), and `type` (e.g., `L` for low tide).

## Configuration

### `src/tidal_variance/config.py` defaults

- `NOAA_API_URL`: `https://api.tidesandcurrents.noaa.gov/api/prod/datagetter`
- `STATION_ID`: `9414131`
- `DAY_START_HOUR`: `10`
- `DAY_END_HOUR`: `16`
- `TIDEPOOL_TIDE`: `0.1`
- `DATA_RAW_DIR`: `data/raw/`
- `DATA_PROCESSED_DIR`: `data/processed/`
- `OUT_PLOTS_DIR`: `out/plots/`

### `API_MODE` defaults (`src/tidal_variance/cli.py`)

- `--source` default: `csv`
- `--csv_path` default: `data/raw/raw_tide_data.csv`
- API date range defaults:
- `start_year = 2019` (`2019-01-01`)
- `end_year = 2024` (`2024-12-31`)
- API product in current code path: `predictions`
- Note: NOAA API generally limits requests to about 5 years per call.

## Outputs

When analysis completes, the project writes:

- Processed CSV files to `data/processed/`
- Plot images (`.png`) to `out/plots/`
- Raw API export to `data/raw/` (when `--source api`)

Output filenames include an inferred year range suffix (for example, `_2019_2024`).

## Testing

Run the test suite:

```bash
pytest -q
```

## Development Notes

- `monthly_tidal_variance.py` is a compatibility entrypoint that imports from `src/tidal_variance/`.
- If a target output CSV already exists, exports rotate the existing file to a timestamped `.bak_*.csv`.
