"""Tidal variance analysis package."""

from .analysis import (
    analyze_daytime_monthly_average,
    analyze_monthly_average,
    calculate_monthly_avg_count_below_tidepool_tide_daytime,
    calculate_monthly_avg_lowest_day_tide_by_year,
    calculate_monthly_avg_lowest_daytime_tide,
    identify_low_tides,
)
from .cli import load_tidal_data, main, parse_args, run_analysis
from .config import (
    DATA_PROCESSED_DIR,
    DATA_RAW_DIR,
    DEFAULT_END_YEAR,
    DEFAULT_START_YEAR,
    DAY_END_HOUR,
    DAY_START_HOUR,
    NOAA_API_URL,
    OUT_PLOTS_DIR,
    STATION_ID,
    TIDEPOOL_TIDE,
)
from .io import (
    append_period_to_filename,
    build_period_suffix,
    ensure_api_token_file,
    ensure_project_directories,
    export_to_csv,
    fetch_tidal_data,
    resolve_input_path,
)
from .plotting import (
    plot_monthly_average,
    plot_monthly_avg_count_below_tidepool_daytime_histogram,
    plot_monthly_avg_lowest_daytime_tide,
    plot_monthly_avg_lowest_tide_by_year,
)

__all__ = [
    "NOAA_API_URL",
    "STATION_ID",
    "DAY_START_HOUR",
    "DAY_END_HOUR",
    "DEFAULT_START_YEAR",
    "DEFAULT_END_YEAR",
    "TIDEPOOL_TIDE",
    "DATA_RAW_DIR",
    "DATA_PROCESSED_DIR",
    "OUT_PLOTS_DIR",
    "ensure_project_directories",
    "ensure_api_token_file",
    "fetch_tidal_data",
    "identify_low_tides",
    "analyze_monthly_average",
    "analyze_daytime_monthly_average",
    "build_period_suffix",
    "append_period_to_filename",
    "plot_monthly_average",
    "calculate_monthly_avg_lowest_daytime_tide",
    "plot_monthly_avg_lowest_daytime_tide",
    "calculate_monthly_avg_lowest_day_tide_by_year",
    "plot_monthly_avg_lowest_tide_by_year",
    "calculate_monthly_avg_count_below_tidepool_tide_daytime",
    "plot_monthly_avg_count_below_tidepool_daytime_histogram",
    "export_to_csv",
    "resolve_input_path",
    "parse_args",
    "load_tidal_data",
    "run_analysis",
    "main",
]
