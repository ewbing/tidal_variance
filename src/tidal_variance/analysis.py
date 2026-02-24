"""Data analysis helpers for tidal variance."""

from datetime import datetime

import pandas as pd

from .config import DATA_PROCESSED_DIR, DAY_END_HOUR, DAY_START_HOUR, TIDEPOOL_TIDE
from .io import export_to_csv


def identify_low_tides(df):
    """Identify lower-low tides as local minima among consecutive low-tide points."""
    low_tides = df[df["type"] == "L"].sort_values("t").reset_index(drop=True).copy()
    if len(low_tides) <= 1:
        return low_tides.copy()

    padded = pd.concat(
        [low_tides.iloc[[1]], low_tides, low_tides.iloc[[-2]]],
        ignore_index=True,
    )
    interior_mask = (padded["v"] < padded["v"].shift(1)) & (padded["v"] < padded["v"].shift(-1))
    mask = interior_mask.iloc[1:-1].reset_index(drop=True)
    return low_tides[mask].reset_index(drop=True)


def analyze_monthly_average(low_tides_df):
    """Return average lowest tide per month."""
    df_local = low_tides_df.copy()
    df_local["month"] = df_local["t"].dt.month
    monthly_avg = df_local.groupby("month")["v"].mean().reset_index()
    monthly_avg["month_name"] = monthly_avg["month"].apply(
        lambda month: datetime(1900, month, 1).strftime("%B")
    )
    return monthly_avg


def analyze_daytime_monthly_average(low_tides_df, start_hour=10, end_hour=16):
    """Return average low tide per month within a specified daytime window."""
    df_local = low_tides_df.copy()
    df_local["hour"] = df_local["t"].dt.hour
    filtered_df = df_local[(df_local["hour"] >= start_hour) & (df_local["hour"] <= end_hour)]

    if filtered_df.empty:
        print("No low tides found within the specified time window.")
        return pd.DataFrame()

    filtered_df["month"] = filtered_df["t"].dt.month
    monthly_avg_window = filtered_df.groupby("month")["v"].mean().reset_index()
    monthly_avg_window["month_name"] = monthly_avg_window["month"].apply(
        lambda month: datetime(1900, month, 1).strftime("%B")
    )
    return monthly_avg_window


def calculate_monthly_avg_lowest_daytime_tide(df):
    """Calculate average lowest daytime tide each month across all years."""
    df_filtered = df[(df["t"].dt.hour >= DAY_START_HOUR) & (df["t"].dt.hour <= DAY_END_HOUR)].copy()
    df_filtered["month"] = df_filtered["t"].dt.month

    monthly_avg_lowest = df_filtered.groupby("month")["v"].mean().reset_index()
    monthly_avg_lowest["month_name"] = monthly_avg_lowest["month"].apply(
        lambda month: datetime(1900, month, 1).strftime("%B")
    )
    monthly_avg_lowest.rename(columns={"v": "average_lowest_tide"}, inplace=True)
    return monthly_avg_lowest


def calculate_monthly_avg_lowest_day_tide_by_year(
    df,
    output_filename=DATA_PROCESSED_DIR / "monthly_avg_lowest_tide_by_year.csv",
):
    """Calculate average lowest daytime tide each month per year and export CSV."""
    df_filtered = df[(df["t"].dt.hour >= DAY_START_HOUR) & (df["t"].dt.hour <= DAY_END_HOUR)].copy()
    df_filtered["year"] = df_filtered["t"].dt.year
    df_filtered["month"] = df_filtered["t"].dt.month

    monthly_avg_lowest_yearly = df_filtered.groupby(["year", "month"])["v"].mean().reset_index()
    monthly_avg_lowest_yearly["month_name"] = monthly_avg_lowest_yearly["month"].apply(
        lambda month: datetime(1900, month, 1).strftime("%B")
    )
    monthly_avg_lowest_yearly.rename(columns={"v": "average_lowest_tide"}, inplace=True)

    export_to_csv(monthly_avg_lowest_yearly, output_filename)
    return monthly_avg_lowest_yearly


def calculate_monthly_avg_count_below_tidepool_tide_daytime(
    df,
    output_filename=DATA_PROCESSED_DIR / "monthly_avg_count_below_tidepool_daytime.csv",
):
    """Calculate average monthly daytime counts below the tidepool threshold."""
    df_local = df.copy()
    df_local["t"] = pd.to_datetime(df_local["t"])

    df_local["month"] = df_local["t"].dt.month
    df_local["year"] = df_local["t"].dt.year
    df_local["hour"] = df_local["t"].dt.hour

    df_below = df_local[df_local["v"] < TIDEPOOL_TIDE].copy()
    df_below_daytime = df_below[(df_below["hour"] >= DAY_START_HOUR) & (df_below["hour"] < DAY_END_HOUR)]

    monthly_counts_daytime = (
        df_below_daytime.groupby(["year", "month"]).size().reset_index(name="count_below_tidepool_tide_daytime")
    )

    average_monthly_counts_daytime = (
        monthly_counts_daytime.groupby("month")["count_below_tidepool_tide_daytime"].mean().reset_index()
    )

    all_months = pd.DataFrame({"month": range(1, 13)})
    average_monthly_counts_daytime = all_months.merge(
        average_monthly_counts_daytime, on="month", how="left"
    ).fillna(0)

    average_monthly_counts_daytime["month_name"] = average_monthly_counts_daytime["month"].apply(
        lambda month: datetime(1900, month, 1).strftime("%B")
    )

    average_monthly_counts_daytime.rename(
        columns={
            "count_below_tidepool_tide_daytime": "average_count_below_tidepool_tide_daytime"
        },
        inplace=True,
    )

    export_to_csv(average_monthly_counts_daytime, output_filename)
    return average_monthly_counts_daytime
