import argparse
from datetime import datetime

import requests
import pandas as pd
import matplotlib.pyplot as plt

# NOAA API Endpoint
NOAA_API_URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"

# Station ID for Pillar Point Harbor
STATION_ID = "9414131"

# NOAA API Token (if required for observed data)
API_TOKEN = "YOUR_NOAA_API_TOKEN"  # Replace with your actual token


def fetch_tidal_data(station_id, start_date, end_date, product="predictions"):
    """
    Fetch tidal data from NOAA API.

    Args:
        station_id (str): NOAA station ID.
        start_date (datetime): Start date.
        end_date (datetime): End date.
        product (str): 'predictions' or 'water_level'.

    Returns:
        pd.DataFrame: Tidal data.
    """
    params = {
        "product": product,
        "application": "web_services",
        "begin_date": start_date.strftime("%Y%m%d"),
        "end_date": end_date.strftime("%Y%m%d"),
        "datum": "MLLW",
        "station": station_id,
        "time_zone": "GMT",
        "units": "metric",
        "interval": "h",
        "format": "json",
    }

    if product == "water_level":
        params["token"] = API_TOKEN  # Include token for observed data

    response = requests.get(NOAA_API_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    key = "water_level" if product == "water_level" else "predictions"
    if key not in data:
        raise ValueError(f"Unexpected response format: {data}")

    df = pd.DataFrame(data[key])
    df["t"] = pd.to_datetime(df["t"])
    df["v"] = pd.to_numeric(df["v"])
    return df


def identify_low_tides(df):
    """
    Identify low tides by finding local minima in the tidal data.

    Args:
        df (pd.DataFrame): Tidal data sorted by time.

    Returns:
        pd.DataFrame: DataFrame containing only low tides.
    """
    df = df.sort_values("t").reset_index(drop=True)
    low_tides = []

    for i in range(1, len(df) - 1):
        if df.loc[i, "v"] < df.loc[i - 1, "v"] and df.loc[i, "v"] < df.loc[i + 1, "v"]:
            low_tides.append(df.loc[i])

    return pd.DataFrame(low_tides)


def analyze_monthly_variance(low_tides_df):
    """
    Analyze monthly variance in low tide data.

    Args:
        low_tides_df (pd.DataFrame): DataFrame containing low tides.

    Returns:
        pd.DataFrame: Average low tide per month.
    """
    low_tides_df["month"] = low_tides_df["t"].dt.month
    monthly_avg = low_tides_df.groupby("month")["v"].mean().reset_index()
    monthly_avg["month_name"] = monthly_avg["month"].apply(
        lambda x: datetime(1900, x, 1).strftime("%B")
    )
    return monthly_avg


def analyze_variance_time_window(low_tides_df, start_hour=9, end_hour=16):
    """
    Analyze monthly variance of low tides between specified hours.

    Args:
        low_tides_df (pd.DataFrame): DataFrame containing low tides.
        start_hour (int): Start hour in 24-hour format.
        end_hour (int): End hour in 24-hour format.

    Returns:
        pd.DataFrame: Average low tide per month within the time window.
    """
    # Filter low tides within the specified time window
    low_tides_df["hour"] = low_tides_df["t"].dt.hour
    filtered_df = low_tides_df[
        (low_tides_df["hour"] >= start_hour) & (low_tides_df["hour"] <= end_hour)
    ]

    if filtered_df.empty:
        print("No low tides found within the specified time window.")
        return pd.DataFrame()

    # Calculate monthly average low tides
    filtered_df["month"] = filtered_df["t"].dt.month
    monthly_avg_window = filtered_df.groupby("month")["v"].mean().reset_index()
    monthly_avg_window["month_name"] = monthly_avg_window["month"].apply(
        lambda x: datetime(1900, x, 1).strftime("%B")
    )

    return monthly_avg_window


def plot_monthly_variance(
    monthly_avg, title="Average Mean Low Tide per Month at Pillar Point Harbor"
):
    """Plot the monthly variance of mean low tides."""
    plt.figure(figsize=(10, 6))
    plt.bar(monthly_avg["month_name"], monthly_avg["v"], color="skyblue")
    plt.title(title)
    plt.xlabel("Month")
    plt.ylabel("Average Low Tide Level (m)")
    plt.xticks(rotation=45)
    plt.grid(axis="y")
    plt.tight_layout()
    plt.show()


def plot_lowest_tide(monthly_avg_window):
    """
    Plot the lowest tide per month within the specified time window.

    Args:
        monthly_avg_window (pd.DataFrame): DataFrame containing monthly average low tides within the time window.
    """
    plt.figure(figsize=(10, 6))
    plt.bar(monthly_avg_window["month_name"], monthly_avg_window["v"], color="skyblue")
    plt.title("Lowest Tide per Month (9AM - 4PM)")
    plt.xlabel("Month")
    plt.ylabel("Lowest Tide Level (m)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("lowest_tide_per_month.png")  # Saves the plot as an image file
    plt.show()


def calculate_monthly_avg_lowest_tide(df):
    """
    Calculate the average lowest tide each month across all years between 9 AM and 4 PM.

    Args:
        df (pd.DataFrame): DataFrame containing low tide data with 't' and 'v' columns.

    Returns:
        pd.DataFrame: DataFrame with 'month', 'average_lowest_tide', and 'month_name' columns.
    """
    # Filter tides between 9 AM and 4 PM
    df_filtered = df[(df["t"].dt.hour >= 9) & (df["t"].dt.hour <= 16)].copy()

    # Extract month from datetime
    df_filtered["month"] = df_filtered["t"].dt.month

    # Calculate monthly average lowest tide
    monthly_avg_lowest = df_filtered.groupby("month")["v"].mean().reset_index()

    # Add month names for readability
    monthly_avg_lowest["month_name"] = monthly_avg_lowest["month"].apply(
        lambda x: datetime(1900, x, 1).strftime("%B")
    )

    # Rename columns for clarity
    monthly_avg_lowest.rename(columns={"v": "average_lowest_tide"}, inplace=True)

    return monthly_avg_lowest


def plot_monthly_avg_lowest_tide(
    monthly_avg_lowest, title="Average of Monthly Lowest Tide in day time"
):
    """
    Plot the average lowest tide each month.

    Args:
        monthly_avg_lowest (pd.DataFrame): DataFrame containing average lowest tide per month.
        title (str): Title of the plot.
    """
    plt.figure(figsize=(10, 6))
    plt.bar(
        monthly_avg_lowest["month_name"],
        monthly_avg_lowest["average_lowest_tide"],
        color="salmon",
    )
    plt.title(title)
    plt.xlabel("Month")
    plt.ylabel("Average Lowest Tide Level (m)")
    plt.xticks(rotation=45)
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig("average_lowest_tide_per_month.png")  # Saves the plot as an image file
    plt.show()


def export_to_csv(df, filename):
    """
    Export DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): DataFrame to export.
        filename (str): Name of the CSV file.
    """
    df.to_csv(filename, index=False)
    print(f"Data exported to {filename}")


def main():

    parser = argparse.ArgumentParser(description="Process tidal data.")
    parser.add_argument(
        "--source",
        choices=["api", "csv"],
        default="csv",
        help="Data source: 'api' to fetch from API, 'csv' to read from detailed CSV file.",
    )
    parser.add_argument(
        "--csv_path",
        type=str,
        default="detailed_low_tide_data.csv",
        help="Path to the detailed low tide CSV file.",
    )
    args = parser.parse_args()

    # Define the analysis period
    # TODO: Update the start and end years from data when pulling from csv
    start_year = 2014
    end_year = 2024
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)

    print(
        f"Analysis period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )

    if args.source == "csv":
        try:
            print(f"Reading detailed low tide data from {args.csv_path}...")
            low_tides_df = pd.read_csv(
                args.csv_path, parse_dates=["t"]
            )  # Adjust 't' if the date column has a different name
            print("Data successfully loaded from CSV.")
        except FileNotFoundError:
            print(f"Error: The file {args.csv_path} does not exist.")
            return
        except pd.errors.ParserError:
            print(f"Error: Could not parse the CSV file {args.csv_path}.")
            return
    else:
        try:

            # Fetch tidal data
            print("Fetching tidal data...")
            tidal_df = fetch_tidal_data(
                STATION_ID, start_date, end_date, product="predictions"
            )

            # Identify low tides
            print("Identifying low tides...")
            low_tides_df = identify_low_tides(tidal_df)

            if low_tides_df.empty:
                print("No low tides identified in the data.")
                return

            # Export detailed low tide data to CSV
            print("Exporting detailed low tide data to CSV...")
            export_to_csv(low_tides_df, "detailed_low_tide_data.csv")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching data: {e}")
        except ValueError as e:
            print(f"An error occurred with data processing: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return

    try:
        # Analyze monthly variance
        print("Analyzing monthly variance...")
        monthly_avg = analyze_monthly_variance(low_tides_df)

        # Export analyzed data to CSV
        print("Exporting data to CSV...")
        export_to_csv(monthly_avg, "monthly_low_tide_variance.csv")

        # Plot the overall monthly variance
        print("Plotting overall monthly variance...")
        plot_monthly_variance(
            monthly_avg,
            title="Average Low Tide per Month at Pillar Point Harbor between "
            + str(start_year)
            + " and "
            + str(end_year),
        )

        # Analyze variance between 9AM and 4PM
        print("Analyzing variance between 9AM and 4PM...")
        monthly_avg_window = analyze_variance_time_window(
            low_tides_df, start_hour=9, end_hour=16
        )

        if not monthly_avg_window.empty:
            # Export time window variance data to CSV
            print("Exporting time window variance data to CSV...")
            export_to_csv(monthly_avg_window, "monthly_low_tide_variance_9AM_4PM.csv")

            # Plot the time window variance
            print("Plotting time window variance...")
            plot_monthly_variance(
                monthly_avg_window,
                title="Average Low Tide per Month (9AM - 4PM) at Pillar Point Harbor between "
                + str(start_year)
                + " and "
                + str(end_year),
            )

        # New Functionality: Calculate and Plot Average Lowest Tide Each Month
        print("Calculating average lowest tide each month across all years...")
        monthly_avg_lowest = calculate_monthly_avg_lowest_tide(low_tides_df)

        print("Exporting average lowest tide data to CSV...")
        export_to_csv(monthly_avg_lowest, "average_lowest_tide_per_month.csv")

        print("Plotting average lowest tide each month...")
        plot_monthly_avg_lowest_tide(monthly_avg_lowest)

    except FileNotFoundError:
        print("Error: The file 'detailed_low_tide_data.csv' does not exist.")
    except pd.errors.ParserError:
        print("Error: Could not parse the CSV file 'detailed_low_tide_data.csv'.")
    except ValueError as e:
        print(f"An error occurred with data processing: {e}")
    except Exception as e:
        print(f"An error occurred during analysis or plotting: {e}")


if __name__ == "__main__":
    main()
