"""CLI entry points for tidal variance analysis."""

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from .analysis import (
    analyze_monthly_average,
    calculate_monthly_avg_count_below_tidepool_tide_daytime,
    calculate_monthly_avg_lowest_day_tide_by_year,
    calculate_monthly_avg_lowest_daytime_tide,
    identify_low_tides,
)
from .config import (
    DATA_PROCESSED_DIR,
    DATA_RAW_DIR,
    DEFAULT_END_YEAR,
    DEFAULT_START_YEAR,
    OUT_PLOTS_DIR,
    STATION_ID,
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


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Process tidal data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--source",
        choices=["api", "csv"],
        default="csv",
        help="Data source: 'api' to fetch from API, 'csv' to read from detailed CSV file.",
    )
    parser.add_argument(
        "--csv_path",
        type=str,
        default=str(DATA_RAW_DIR / "raw_tide_data.csv"),
        help="Path to the detailed low tide CSV file (used only when --source csv).",
    )
    parser.add_argument(
        "--api_raw_output",
        type=str,
        default="raw_tide_data.csv",
        help=(
            "Base filename or path for raw API export. Year suffix is appended "
            "automatically (for example, raw_tide_data_2019_2024.csv)."
        ),
    )
    return parser.parse_args()


def load_tidal_data(args):
    """Load tide data from CSV or NOAA API and return period metadata."""
    ensure_project_directories()
    start_year = DEFAULT_START_YEAR
    end_year = DEFAULT_END_YEAR
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)

    tidal_df = pd.DataFrame()
    if args.source == "csv":
        try:
            project_root = Path(__file__).resolve().parents[2]
            resolved_csv_path = resolve_input_path(args.csv_path, base_dir=project_root)
            if resolved_csv_path is None:
                print(f"Error: The file {args.csv_path} does not exist.")
                print(f"Current working directory: {Path.cwd()}")
                print(f"Project root: {project_root}")
                return None, start_year, end_year

            print(f"Reading detailed tidal data from {resolved_csv_path}...")
            tidal_df = pd.read_csv(resolved_csv_path, parse_dates=["t"])
            print("Data successfully loaded from CSV.")

            start_date = tidal_df["t"].min()
            end_date = tidal_df["t"].max()
            start_year = start_date.year
            end_year = end_date.year

            print(
                f"Analysis period: {start_date.strftime('%Y-%m-%d')} "
                f"to {end_date.strftime('%Y-%m-%d')}"
            )
        except FileNotFoundError:
            print(f"Error: The file {args.csv_path} does not exist.")
            return None, start_year, end_year
        except pd.errors.ParserError:
            print(f"Error: Could not parse the CSV file {args.csv_path}.")
            return None, start_year, end_year
    else:
        ensure_api_token_file()
        try:
            print(
                f"Analysis period: {start_date.strftime('%Y-%m-%d')} to "
                f"{end_date.strftime('%Y-%m-%d')}"
            )

            print("Fetching tidal data...")
            # TODO: Add a --product CLI argument and pass it through here instead of hardcoding.
            tidal_df = fetch_tidal_data(STATION_ID, start_date, end_date, product="predictions")

            print("Exporting detailed raw tide data to CSV...")
            raw_output = Path(args.api_raw_output).expanduser()
            if not raw_output.suffix:
                raw_output = raw_output.with_suffix(".csv")
            if not raw_output.is_absolute():
                raw_output = DATA_RAW_DIR / raw_output
            raw_output = append_period_to_filename(
                raw_output,
                build_period_suffix(start_year, end_year),
            )
            export_to_csv(tidal_df, raw_output)

        except requests.exceptions.RequestException as exc:
            print(f"An error occurred while fetching data: {exc}")
            return None, start_year, end_year
        except ValueError as exc:
            print(f"An error occurred with data processing: {exc}")
            return None, start_year, end_year

    return tidal_df, start_year, end_year


def run_analysis(tidal_df, start_year, end_year):
    """Analyze low tides, export CSVs, and generate plots."""
    ensure_project_directories()
    try:
        period_suffix = build_period_suffix(start_year, end_year)
        print("Identifying lower-low tides...")
        low_tides_df = identify_low_tides(tidal_df)

        if low_tides_df.empty:
            print("No low tides identified in the data.")
            return

        print("Exporting detailed low tide data to CSV...")
        output_filename = append_period_to_filename(
            DATA_PROCESSED_DIR / "detailed_low_tide_data.csv",
            period_suffix,
        )
        export_to_csv(low_tides_df, output_filename)

        print("Cacluate average low tide per month...")
        monthly_avg = analyze_monthly_average(low_tides_df)

        print("Exporting data to CSV...")
        export_to_csv(
            monthly_avg,
            append_period_to_filename(
                DATA_PROCESSED_DIR / "monthly_low_tide_average.csv",
                period_suffix,
            ),
        )

        print("Plotting overall monthly variance...")
        plot_monthly_average(
            monthly_avg,
            title=(
                "Average Low Tide per Month at Pillar Point Harbor between "
                f"{start_year} and {end_year}"
            ),
            output_filename=append_period_to_filename(
                OUT_PLOTS_DIR / "average_lowest_tide_per_month.png",
                period_suffix,
            ),
        )

        print("Calculating average lowest tide each month across all years...")
        monthly_avg_lowest = calculate_monthly_avg_lowest_daytime_tide(low_tides_df)

        print("Exporting average lowest tide data to CSV...")
        export_to_csv(
            monthly_avg_lowest,
            append_period_to_filename(
                DATA_PROCESSED_DIR / "average_lowest_daytime_tide_per_month.csv",
                period_suffix,
            ),
        )

        print("Plotting average lowest tide each month...")
        plot_monthly_avg_lowest_daytime_tide(
            monthly_avg_lowest,
            title="Average of Monthly Lowest Daytime Tide",
            output_filename=append_period_to_filename(
                OUT_PLOTS_DIR / "average_lowest_daytime_tide_per_month.png",
                period_suffix,
            ),
        )

        print("Calculating and plotting average lowest tide each month per year...")
        monthly_avg_lowest_yearly = calculate_monthly_avg_lowest_day_tide_by_year(
            low_tides_df,
            output_filename=append_period_to_filename(
                DATA_PROCESSED_DIR / "monthly_avg_lowest_tide_by_year.csv",
                period_suffix,
            ),
        )
        plot_monthly_avg_lowest_tide_by_year(
            monthly_avg_lowest_yearly,
            title="Average Monthly Lowest Day Tide by Year",
            output_filename=append_period_to_filename(
                OUT_PLOTS_DIR / "average_lowest_day_tide_by_year.png",
                period_suffix,
            ),
        )

        average_monthly_counts_daytime = calculate_monthly_avg_count_below_tidepool_tide_daytime(
            low_tides_df,
            output_filename=append_period_to_filename(
                DATA_PROCESSED_DIR / "monthly_avg_count_below_tidepool_daytime.csv",
                period_suffix,
            ),
        )

        plot_monthly_avg_count_below_tidepool_daytime_histogram(
            average_monthly_counts_daytime,
            title=(
                "Average Monthly Count of Tidepool Tides During Daytime "
                f"({start_year} to {end_year})"
            ),
            output_filename=append_period_to_filename(
                OUT_PLOTS_DIR / "average_count_below_tidepool_tide_daytime_histogram.png",
                period_suffix,
            ),
        )
    except pd.errors.ParserError:
        print("Error: Could not parse the CSV file.")
    except ValueError as exc:
        print(f"An error occurred with data processing: {exc}")
    except (KeyError, TypeError) as exc:
        print(f"An error occurred during analysis or plotting: {exc}")


def main():
    """Parse inputs, load data, and run tidal variance analysis."""
    args = parse_args()
    tidal_df, start_year, end_year = load_tidal_data(args)
    if tidal_df is None or tidal_df.empty:
        print("No tidal data available for analysis.")
        return

    run_analysis(tidal_df, start_year, end_year)


if __name__ == "__main__":
    main()
