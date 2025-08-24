import argparse
import calendar
from datetime import datetime

import os
import requests
import pandas as pd
import matplotlib.pyplot as plt

# NOAA API Endpoint
NOAA_API_URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"

# Station ID for Pillar Point Harbor
STATION_ID = "9414131"
# Define day start and end hours
DAY_START_HOUR=10
DAY_END_HOUR=16

# Highest tidepooling tide
TIDEPOOL_TIDE=.1

# Attempt to import API_TOKEN from api_token.py
try:
    from api_token import API_TOKEN
except (ImportError, AttributeError):
    API_TOKEN = None
    print("Warning: API_TOKEN not found. 'water_level' data will not be available.")

if API_TOKEN is None:
    if not os.path.exists("api_token.py"):
        with open("api_token.py", "w", encoding="utf-8") as f:
            f.write('''# api_token.py
                    API_TOKEN = "YOUR_NOAA_API_TOKEN"  # Replace with your actual token\n''')
        print("Created 'api_token.py'. Please add your API_TOKEN to this file.")
    else:
        print("'api_token.py' exists but API_TOKEN is not defined. Please add your API_TOKEN.")

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
        "time_zone": "lst_ldt",
        "units": "english",
        "interval": "hilo",
        "format": "json",
    }

    if product == "water_level":
        if API_TOKEN:
            if API_TOKEN == "YOUR_NOAA_API_TOKEN":
                print("Warning: API_TOKEN not defined. Should be set in api_token.py. ",
                "Cannot fetch 'water_level' data.")
                return pd.DataFrame()  # Return an empty DataFrame or handle as needed
            else:
                params["token"] = API_TOKEN  # Use the imported token
        else:
            print("Error: API_TOKEN is not available. Cannot fetch 'water_level' data.")
            return pd.DataFrame()  # Return an empty DataFrame or handle as needed

    try:
        response = requests.get(NOAA_API_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return pd.DataFrame()
    except ValueError as ve:
        print(f"JSON decoding failed: {ve}")
        return pd.DataFrame()

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
        df (pd.DataFrame): Tidal data with 't' (datetime) and 'v' (tide level) columns
                           as well as 'type' (H for high tide, L for low tide)

    Returns:
        pd.DataFrame: DataFrame containing only low tides.
    """
    # df = df.sort_values("t").reset_index(drop=True)

    # Filter out high tides and sort by time
    df = df[df['type'] != 'H'].sort_values("t").reset_index(drop=True)
    low_tides = []

    for i in range(1, len(df) - 1):
        if df.loc[i, "v"] < df.loc[i - 1, "v"] and df.loc[i, "v"] < df.loc[i + 1, "v"]:
            low_tides.append(df.loc[i])

    return pd.DataFrame(low_tides)


def identify_high_tides(df):
    """
    Identify high tides by finding local maxima in the tidal data.

    Args:
        df (pd.DataFrame): Tidal data with 't' (datetime) and 'v' (tide level) columns
                           as well as 'type' (H for high tide, L for low tide)

    Returns:
        pd.DataFrame: DataFrame containing only high tides.
    """
    # Filter out low tides and sort by time
    df = df[df['type'] != 'L'].sort_values("t").reset_index(drop=True)
    high_tides = []

    for i in range(1, len(df) - 1):
        if df.loc[i, "v"] > df.loc[i - 1, "v"] and df.loc[i, "v"] > df.loc[i + 1, "v"]:
            high_tides.append(df.loc[i])

    return pd.DataFrame(high_tides)

def analyze_monthly_average(low_tides_df):
    """
    Analyze monthly variance in low tide data.
    Returns the average lowest tide per month - regardless of time

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


def analyze_daytime_monthly_average(low_tides_df, start_hour=10, end_hour=16):
    """
    Analyze monthly variance of low tides between specified hours.
    Returns the daily average lowest tide per month

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


def plot_monthly_average(
    monthly_avg, title="Average Low Tide per Month"
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
    plt.savefig("average_lowest_tide_per_month.png")  # Saves the plot as an image file
    plt.show()


def calculate_monthly_avg_lowest_daytime_tide(df):
    """
    Calculate the average lowest daytime tide each month across all years.

    Args:
        df (pd.DataFrame): DataFrame containing low tide data with 't' and 'v' columns.

    Returns:
        pd.DataFrame: DataFrame with 'month', 'average_lowest_tide', and 'month_name' columns.
    """
    # Filter tides to daytime
    df_filtered = df[(df["t"].dt.hour >= DAY_START_HOUR) & (df["t"].dt.hour <= DAY_END_HOUR)].copy()

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


def plot_monthly_avg_lowest_daytime_tide(
    monthly_avg_lowest, title="Average of Monthly Lowest Daytime Tide"
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
    plt.savefig("average_lowest_daytime_tide_per_month.png")  # Saves the plot as an image file
    plt.show()

def calculate_monthly_avg_highest_daytime_tide(df):
    """
    Calculate the average highest daytime tide each month across all years.

    Args:
        df (pd.DataFrame): DataFrame containing high tide data with 't' and 'v' columns.

    Returns:
        pd.DataFrame: DataFrame with 'month', 'average_highest_tide', and 'month_name' columns.
    """
    # Filter tides to daytime
    df_filtered = df[(df["t"].dt.hour >= DAY_START_HOUR) & (df["t"].dt.hour <= DAY_END_HOUR)].copy()

    # Extract month from datetime
    df_filtered["month"] = df_filtered["t"].dt.month

    # Calculate monthly average highest tide
    monthly_avg_highest = df_filtered.groupby("month")["v"].mean().reset_index()

    # Add month names for readability
    monthly_avg_highest["month_name"] = monthly_avg_highest["month"].apply(
        lambda x: datetime(1900, x, 1).strftime("%B")
    )

    # Rename columns for clarity
    monthly_avg_highest.rename(columns={"v": "average_highest_tide"}, inplace=True)

    return monthly_avg_highest


def plot_monthly_avg_highest_daytime_tide(monthly_avg_highest, title="Average of Monthly Highest Daytime Tide"):
    """
    Plot the average highest tide each month.

    Args:
        monthly_avg_highest (pd.DataFrame): DataFrame containing average highest tide per month.
        title (str): Title of the plot.
    """
    plt.figure(figsize=(10, 6))
    plt.bar(
        monthly_avg_highest["month_name"],
        monthly_avg_highest["average_highest_tide"],
        color="salmon",
    )
    plt.title(title)
    plt.xlabel("Month")
    plt.ylabel("Average Highest Tide Level (m)")
    plt.xticks(rotation=45)
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig("average_highest_daytime_tide_per_month.png")  # Saves the plot as an image file
    plt.show()

def calculate_monthly_avg_lowest_day_tide_by_year(df, output_filename="monthly_avg_lowest_tide_by_year.csv"):
    """
    Calculate the average lowest daytime tide each month per year.

    Args:
        df (pd.DataFrame): DataFrame containing low tide data with 't' and 'v' columns.

    Returns:
        pd.DataFrame: DataFrame with 'year', 'month', 'average_lowest_tide', and 'month_name' columns.
    """
    # Filter tides between 9 AM and 4 PM
    df_filtered = df[(df["t"].dt.hour >= DAY_START_HOUR) & (df["t"].dt.hour <= DAY_END_HOUR)].copy()

    # Extract year and month from datetime
    df_filtered["year"] = df_filtered["t"].dt.year
    df_filtered["month"] = df_filtered["t"].dt.month

    # Calculate monthly average lowest tide per year
    monthly_avg_lowest_yearly = df_filtered.groupby(["year", "month"])["v"].mean().reset_index()

    # Add month names for readability
    monthly_avg_lowest_yearly["month_name"] = monthly_avg_lowest_yearly["month"].apply(
        lambda x: datetime(1900, x, 1).strftime("%B")
    )

    # Rename columns for clarity
    monthly_avg_lowest_yearly.rename(columns={"v": "average_lowest_tide"}, inplace=True)

    # Export to CSV
    export_to_csv(monthly_avg_lowest_yearly, output_filename)

    return monthly_avg_lowest_yearly

def plot_monthly_avg_lowest_tide_by_year(monthly_avg_lowest_yearly, title="Average Monthly Lowest Day Tide by Year"):
    """
    Plot the average lowest tide each month per year.

    Args:
        monthly_avg_lowest_yearly (pd.DataFrame): DataFrame containing monthly average lowest tides per year.
        title (str): Title of the plot.
    """
    plt.figure(figsize=(12, 8))
    
    # Get unique years
    years = monthly_avg_lowest_yearly['year'].unique()
    
    for year in years:
        yearly_data = monthly_avg_lowest_yearly[monthly_avg_lowest_yearly['year'] == year]
        plt.plot(yearly_data['month_name'], yearly_data['average_lowest_tide'], marker='o', label=str(year))
    
    plt.title(title)
    plt.xlabel("Month")
    plt.ylabel("Average Lowest Tide Level (m)")
    plt.legend(title="Year")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("average_lowest_day_tide_by_year.png")  # Saves the plot as an image file
    plt.show()

def calculate_monthly_avg_count_below_tidepool_tide_daytime(df, output_filename="monthly_avg_count_below_tidepool_daytime.csv"):
    """
    Calculate the average count of tides below TIDEPOOL_TIDE during daytime for each month and export to a CSV file.
    
    Args:
        df (pd.DataFrame): DataFrame containing tidal data with 't' (datetime) and 'v' (tide level) columns.
        output_filename (str): Name of the output CSV file.
    
    Returns:
        pd.DataFrame: DataFrame with 'month', 'average_count_below_tidepool_tide_daytime', and 'month_name' columns.
    """
    # Ensure the datetime column is in datetime format
    df["t"] = pd.to_datetime(df["t"])
    
    # Extract month, year, and hour from datetime
    df["month"] = df["t"].dt.month
    df["year"] = df["t"].dt.year
    df["hour"] = df["t"].dt.hour
    
    # Filter tides below TIDEPOOL_TIDE
    df_below = df[df["v"] < TIDEPOOL_TIDE].copy()
    
    # Further filter to include only tides during daytime hours
    df_below_daytime = df_below[
        (df_below["hour"] >= DAY_START_HOUR) & (df_below["hour"] < DAY_END_HOUR)
    ]
    
    # Count the number of tides below TIDEPOOL_TIDE during daytime per month per year
    monthly_counts_daytime = df_below_daytime.groupby(["year", "month"]).size().reset_index(name="count_below_tidepool_tide_daytime")
    
    # Calculate the average count per month across all years
    average_monthly_counts_daytime = monthly_counts_daytime.groupby("month")["count_below_tidepool_tide_daytime"].mean().reset_index()

    # Create a new DataFrame with all months (1-12)
    all_months = pd.DataFrame({"month": range(1, 13)})

    # Merge the average monthly counts with the all_months DataFrame to include months with 0 results
    average_monthly_counts_daytime = all_months.merge(average_monthly_counts_daytime, on="month", how="left").fillna(0)
    
    # Add month names for readability
    average_monthly_counts_daytime["month_name"] = average_monthly_counts_daytime["month"].apply(
        lambda x: datetime(1900, x, 1).strftime("%B")
    )
    
    # Rename columns for clarity
    average_monthly_counts_daytime.rename(columns={"count_below_tidepool_tide_daytime": "average_count_below_tidepool_tide_daytime"}, inplace=True)
    
    # Export to CSV
    export_to_csv(average_monthly_counts_daytime, output_filename)  # Uses `export_to_csv` from `monthly_tidal_variance.py`
    
    return average_monthly_counts_daytime

def plot_monthly_avg_count_below_tidepool_daytime_histogram(average_monthly_counts_daytime, title="Average Monthly Count of Tidepool Tides During Daytime"):
    """
    Plot a histogram of the average monthly count of tides below TIDEPOOL_TIDE during daytime.
    
    Args:
        average_monthly_counts_daytime (pd.DataFrame): DataFrame containing average monthly counts of tides below TIDEPOOL_TIDE during daytime.
        title (str): Title of the histogram.
    """
    
    # Plot the histogram
    plt.figure(figsize=(10, 6))
    plt.bar(
        average_monthly_counts_daytime["month_name"],
        average_monthly_counts_daytime["average_count_below_tidepool_tide_daytime"],
        color="orchid",
    )
    plt.title(title)
    plt.xlabel("Month")
    plt.ylabel("Average Count of Tides Below " + str(TIDEPOOL_TIDE) + " During Daytime")
    plt.xticks(rotation=45)
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig("average_count_below_tidepool_tide_daytime_histogram.png")  # Saves the plot as an image file
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
        default="raw_tide_data.csv",
        help="Path to the detailed low tide CSV file.",
    )
    args = parser.parse_args()

    # Define the analysis period statically (defaults used if source is api)
    start_year = 2019
    end_year = 2024
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)

    tidal_df = None

    # Bring in data
    if args.source == "csv":
        try:
            print(f"Reading detailed tidal data from {args.csv_path}...")
            tidal_df = pd.read_csv(
                args.csv_path, parse_dates=["t"]
            )  # Adjust 't' if the date column has a different name
            print("Data successfully loaded from CSV.")

            # Set start_year and end_year based on the CSV data
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
            return
        except pd.errors.ParserError:
            print(f"Error: Could not parse the CSV file {args.csv_path}.")
            return
    else:
        try:
            print(
                f"Analysis period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            )

            # Fetch tidal data
            print("Fetching tidal data...")
            tidal_df = fetch_tidal_data(
                STATION_ID, start_date, end_date, product="predictions"
            )

            # Export raw tide data to CSV
            print("Exporting detailed raw tide data to CSV...")
            export_to_csv(tidal_df, "raw_tide_data.csv")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching data: {e}")
        except ValueError as e:
            print(f"An error occurred with data processing: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return


    #Analyze data
    try:

        # Identify low tides
        print("Identifying low tides...")
        low_tides_df = identify_low_tides(tidal_df)

        if low_tides_df.empty:
            print("No low tides identified in the data.")
            return

        # Export detailed low tide data to CSV
        print("Exporting detailed low tide data to CSV...")
        export_to_csv(low_tides_df, "detailed_low_tide_data" + 
                        "_" + str(start_year) + "_" + str(end_year) + ".csv")

        # Analyze monthly variance
        print("Cacluate average low tide per month...")
        monthly_avg = analyze_monthly_average(low_tides_df)

        # Export analyzed data to CSV
        print("Exporting data to CSV...")
        export_to_csv(monthly_avg, "monthly_low_tide_average.csv")

        # Plot the overall monthly variance
        print("Plotting overall monthly variance...")
        plot_monthly_average(
            monthly_avg,
            title="Average Low Tide per Month at Pillar Point Harbor between "
            + str(start_year)
            + " and "
            + str(end_year),
        )

        # # Analyze day time variance
        # print("Cacluate average daytime low tide per month...")
        # monthly_avg_window = analyze_daytime_monthly_average(
        #     low_tides_df, DAY_START_HOUR, DAY_END_HOUR
        # )

        # if not monthly_avg_window.empty:
        #     # Export time window variance data to CSV
        #     print("Exporting time window variance data to CSV...")
        #     export_to_csv(monthly_avg_window, "monthly_daytime_low_tide_average.csv")

        #     # Plot the time window variance
        #     # TODO: Add file name for new plot
        #     print("Plotting time window variance...")
        #     plot_monthly_average(
        #         monthly_avg_window,
        #         title="Average Daytime Low Tide per Month between "
        #         + str(start_year)
        #         + " and "
        #         + str(end_year),
        #     )

        # Calculate and Plot Average Lowest Tide Each Month
        print("Calculating average lowest tide each month across all years...")
        monthly_avg_lowest = calculate_monthly_avg_lowest_daytime_tide(low_tides_df)

        print("Exporting average lowest tide data to CSV...")
        export_to_csv(monthly_avg_lowest, "average_lowest_daytime_tide_per_month.csv")

        print("Plotting average lowest tide each month...")
        plot_monthly_avg_lowest_daytime_tide(monthly_avg_lowest)

        # Calculate and Plot Average Lowest Tide Each Month per Year
        print("Calculating and plotting average lowest tide each month per year...")
        monthly_avg_lowest_yearly = calculate_monthly_avg_lowest_day_tide_by_year(low_tides_df)
        plot_monthly_avg_lowest_tide_by_year(monthly_avg_lowest_yearly)

        # Calculate and export average count of tides below TIDEPOOL_TIDE during daytime
        average_monthly_counts_daytime = calculate_monthly_avg_count_below_tidepool_tide_daytime(low_tides_df)
        
        # Plot the histogram
        plot_monthly_avg_count_below_tidepool_daytime_histogram(
            average_monthly_counts_daytime,
            title="Average Monthly Count of Tidepool Tides During Daytime (" + str(start_year) + " to " + str(end_year) + ")",
            )


        # Identify high tides
        print("Identifying high tides...")
        high_tides_df = identify_high_tides(tidal_df)

        if high_tides_df.empty:
            print("No high tides identified in the data.")
            return

        # Export detailed high tide data to CSV
        print("Exporting detailed high tide data to CSV...")
        export_to_csv(high_tides_df, "detailed_high_tide_data" + 
                        "_" + str(start_year) + "_" + str(end_year) + ".csv")

        # Calculate and Plot Average Highest Tide Each Month
        print("Calculating average highest tide each month across all years...")
        monthly_avg_highest = calculate_monthly_avg_highest_daytime_tide(low_tides_df)

        print("Exporting average highest tide data to CSV...")
        export_to_csv(monthly_avg_highest, "average_highest_daytime_tide_per_month.csv")

        print("Plotting average highest tide each month...")
        plot_monthly_avg_highest_daytime_tide(monthly_avg_highest)




    except pd.errors.ParserError:
        print("Error: Could not parse the CSV file.")
    except ValueError as e:
        print(f"An error occurred with data processing: {e}")
    except Exception as e:
        print(f"An error occurred during analysis or plotting: {e}")


if __name__ == "__main__":
    main()
