# Tidal Variance

Analyze NOAA tide predictions to identify seasonal patterns for good tide pooling.
Focus on daytime low-tide patterns, generate monthly summaries, and export charts/CSVs for exploration.

## Features

- Load tide data from `CSV` files (default)
- Fetch tide data from NOAA API (`predictions` in current CLI flow)
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

>`monthly_tidal_variance.py [-h] [--source {api,csv}] [--csv_path CSV_PATH] [--api_raw_output API_RAW_OUTPUT]`

### Options

```text
  -h, --help            show this help message and exit
  --source {api,csv}    Data source: 'api' to fetch from API, 'csv' to read from detailed CSV file. (default: csv)
  --csv_path CSV_PATH   Path to the detailed low tide CSV file (used only when --source csv). (default:
                        data/raw/raw_tide_data.csv)
  --api_raw_output API_RAW_OUTPUT
                        Base filename or path for raw API export. Year suffix is appended automatically (for example,
                        raw_tide_data_2019_2024.csv). (default: raw_tide_data.csv)
```

## Examples

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

### Run from NOAA API with explicit raw output name

```bash
python monthly_tidal_variance.py \
  --source api \
  --api_raw_output data/raw/raw_tide_data.csv
```

This produces `data/raw/raw_tide_data_2019_2024.csv` with the default year range.

### NOAA token setup (optional, recommended)

The generic `api_token.py` file contains:

```python
API_TOKEN = "YOUR_NOAA_API_TOKEN"  # Replace with your actual token
```

Replace the placeholder with your NOAA token to enable higher-throughput NOAA requests. The current CLI path fetches `predictions`.

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
- `DEFAULT_START_YEAR`: `2019`
- `DEFAULT_END_YEAR`: `2024`
- `DATA_RAW_DIR`: `data/raw/`
- `DATA_PROCESSED_DIR`: `data/processed/`
- `OUT_PLOTS_DIR`: `out/plots/`

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
