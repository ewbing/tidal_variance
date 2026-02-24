"""Plotting helpers for tidal variance analysis."""

import matplotlib.pyplot as plt

from .config import OUT_PLOTS_DIR, TIDEPOOL_TIDE


def plot_monthly_average(
    monthly_avg,
    title="Average Low Tide per Month",
    output_filename=OUT_PLOTS_DIR / "average_lowest_tide_per_month.png",
):
    """Plot monthly mean low tides."""
    plt.figure(figsize=(10, 6))
    plt.bar(monthly_avg["month_name"], monthly_avg["v"], color="skyblue")
    plt.title(title)
    plt.xlabel("Month")
    plt.ylabel("Average Low Tide Level (ft)")
    plt.xticks(rotation=45)
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig(output_filename)
    plt.show()


def plot_monthly_avg_lowest_daytime_tide(
    monthly_avg_lowest,
    title="Average of Monthly Lowest Daytime Tide",
    output_filename=OUT_PLOTS_DIR / "average_lowest_daytime_tide_per_month.png",
):
    """Plot average lowest daytime tide for each month."""
    plt.figure(figsize=(10, 6))
    plt.bar(
        monthly_avg_lowest["month_name"],
        monthly_avg_lowest["average_lowest_tide"],
        color="salmon",
    )
    plt.title(title)
    plt.xlabel("Month")
    plt.ylabel("Average Lowest Tide Level (ft)")
    plt.xticks(rotation=45)
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig(output_filename)
    plt.show()


def plot_monthly_avg_lowest_tide_by_year(
    monthly_avg_lowest_yearly,
    title="Average Monthly Lowest Day Tide by Year",
    output_filename=OUT_PLOTS_DIR / "average_lowest_day_tide_by_year.png",
):
    """Plot average monthly lowest day tide by year."""
    plt.figure(figsize=(12, 8))

    years = monthly_avg_lowest_yearly["year"].unique()
    for year in years:
        yearly_data = monthly_avg_lowest_yearly[monthly_avg_lowest_yearly["year"] == year]
        plt.plot(
            yearly_data["month_name"],
            yearly_data["average_lowest_tide"],
            marker="o",
            label=str(year),
        )

    plt.title(title)
    plt.xlabel("Month")
    plt.ylabel("Average Lowest Tide Level (ft)")
    plt.legend(title="Year")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_filename)
    plt.show()


def plot_monthly_avg_count_below_tidepool_daytime_histogram(
    average_monthly_counts_daytime,
    title="Average Monthly Count of Tidepool Tides During Daytime",
    output_filename=OUT_PLOTS_DIR / "average_count_below_tidepool_tide_daytime_histogram.png",
):
    """Plot monthly average count of daytime tides below tidepool threshold."""
    plt.figure(figsize=(10, 6))
    plt.bar(
        average_monthly_counts_daytime["month_name"],
        average_monthly_counts_daytime["average_count_below_tidepool_tide_daytime"],
        color="orchid",
    )
    plt.title(title)
    plt.xlabel("Month")
    plt.ylabel(f"Average Count of Tides Below {TIDEPOOL_TIDE} During Daytime")
    plt.xticks(rotation=45)
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig(output_filename)
    plt.show()
