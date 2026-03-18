# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run (CSV source)
python monthly_tidal_variance.py --source csv --csv_path data/raw/raw_tide_data.csv

# Run (NOAA API, saves raw output)
python monthly_tidal_variance.py --source api --api_raw_output data/raw/raw_tide_data.csv

# Test
pytest -q

# Run single test
pytest tests/test_monthly_tidal_variance.py::MonthlyTidalVarianceTests::test_identify_low_tides_returns_expected_lower_low_points -v

# Lint
pylint src/
```

## Architecture

**Tidal Variance** analyzes NOAA tide prediction data to identify seasonal patterns for tide pooling. It fetches or loads tide data, identifies low-tide windows during daytime hours, aggregates by month/year, and produces CSV exports + Matplotlib charts.

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| `src/tidal_variance/config.py` | All constants: station ID, thresholds, year range, directory paths anchored to project root |
| `src/tidal_variance/io.py` | NOAA API client, CSV export with file rotation, path resolution, directory creation |
| `src/tidal_variance/analysis.py` | Pure Pandas/NumPy transformations: local minima detection, monthly aggregations, tidepool count zero-filling |
| `src/tidal_variance/plotting.py` | Matplotlib bar/line charts; receives pre-computed DataFrames, no side effects |
| `src/tidal_variance/cli.py` | `parse_args`, `load_tidal_data`, `run_analysis`, `main` — orchestrates the full pipeline |
| `monthly_tidal_variance.py` | Backwards-compatible root-level entry point; adds `src/` to `sys.path` and re-exports everything |

### Data Pipeline

```
CLI args → parse_args() → load_tidal_data()
                               ↓ (CSV or NOAA API fetch)
                         Raw DataFrame (columns: t, v, type)
                               ↓
                         identify_low_tides()   ← local minima with padding
                               ↓
                         6 analyze_*() functions
                               ↓
                         4 CSV exports + 4 PNG plots
```

### Key Behaviors

- **Path anchoring**: All paths resolve relative to `Path(__file__).resolve().parents[N]` so the same code works from CLI, VSCode debugger, and `pytest`.
- **File rotation**: `export_to_csv()` renames existing files to `.bak_<timestamp>.csv` before overwriting.
- **Output suffixing**: All output filenames include a `YYYY_YYYY` period suffix (e.g., `low_tides_2019_2024.csv`).
- **Zero-filling**: The tidepool count analysis ensures all 12 months are present even if some have no observations.
- **Daytime window**: Daytime filtering uses `DAY_START_HOUR=10` to `DAY_END_HOUR=16` (configurable in `config.py`).
- **Tidepool threshold**: `TIDEPOOL_TIDE=0.1` ft — tides at or below this are counted as tidepool-accessible.

### Default Configuration (config.py)

- Station: Pillar Point Harbor, CA (`9414131`)
- Year range: 2019–2024
- Daytime: 10:00–16:00
- Tidepool threshold: 0.1 ft
- Outputs: `data/processed/` (CSVs), `out/plots/` (PNGs)

### Tests

`tests/test_monthly_tidal_variance.py` — `MonthlyTidalVarianceTests` class using January 2024 fixture data (`tests/fixtures/raw_tide_data_subset.csv`). Tests cover: local minima detection, monthly averaging, 12-month zero-filling, and file rotation.

### NOAA API Token

Place token in `api_token.py` at project root (git-ignored). The `ensure_api_token_file()` function in `io.py` creates a template if missing.
