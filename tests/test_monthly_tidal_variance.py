"""Tests for monthly_tidal_variance core analysis functions."""

import tempfile
import unittest
from pathlib import Path

import pandas as pd

import monthly_tidal_variance as mtv


class MonthlyTidalVarianceTests(unittest.TestCase):
    """Validate tide filtering and monthly aggregation behavior."""

    @classmethod
    def setUpClass(cls):
        fixture_path = Path(__file__).parent / "fixtures" / "raw_tide_data_subset.csv"
        cls.raw_df = pd.read_csv(fixture_path, parse_dates=["t"])
        cls.low_tides_df = mtv.identify_low_tides(cls.raw_df)

    def test_identify_low_tides_returns_expected_lower_low_points(self):
        """Lower-low detection should produce the expected sequence for fixture input."""
        self.assertTrue((self.low_tides_df["type"] == "L").all())
        self.assertEqual(len(self.low_tides_df), 10)

        expected_levels = [1.696, 1.258, 0.799, 0.354, -0.043, -0.368, -0.604, -0.739, -0.760, -0.656]
        self.assertListEqual(self.low_tides_df["v"].round(3).tolist(), expected_levels)

    def test_analyze_monthly_average_returns_expected_january_mean(self):
        """Monthly average for the fixture should contain January with expected mean."""
        monthly_avg = mtv.analyze_monthly_average(self.low_tides_df)

        self.assertEqual(len(monthly_avg), 1)
        self.assertEqual(monthly_avg.loc[0, "month"], 1)
        self.assertEqual(monthly_avg.loc[0, "month_name"], "January")
        self.assertAlmostEqual(monthly_avg.loc[0, "v"], 0.0937, places=4)

    def test_count_below_tidepool_daytime_includes_all_months(self):
        """Daytime tidepool counts should include all months and zero-fill missing months."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "counts.csv"
            result = mtv.calculate_monthly_avg_count_below_tidepool_tide_daytime(
                self.low_tides_df,
                output_filename=str(output_path),
            )

            self.assertTrue(output_path.exists())
            self.assertEqual(len(result), 12)
            self.assertListEqual(result["month"].tolist(), list(range(1, 13)))

            january_count = result.loc[
                result["month"] == 1,
                "average_count_below_tidepool_tide_daytime",
            ].iloc[0]
            self.assertEqual(january_count, 3.0)

            other_months_nonzero = result.loc[
                result["month"] != 1,
                "average_count_below_tidepool_tide_daytime",
            ].sum()
            self.assertEqual(other_months_nonzero, 0.0)

    def test_export_to_csv_renames_existing_file(self):
        """Existing output CSV should be renamed before writing a new file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "raw_tide_data_2019_2024.csv"
            df_initial = pd.DataFrame({"t": [pd.Timestamp("2024-01-01 12:00:00")], "v": [1.0]})
            df_updated = pd.DataFrame({"t": [pd.Timestamp("2024-01-02 12:00:00")], "v": [2.0]})

            mtv.export_to_csv(df_initial, output_path)
            mtv.export_to_csv(df_updated, output_path)

            rotated_files = list(output_path.parent.glob("raw_tide_data_2019_2024.bak_*.csv"))
            self.assertEqual(len(rotated_files), 1)

            current_df = pd.read_csv(output_path, parse_dates=["t"])
            self.assertAlmostEqual(current_df.loc[0, "v"], 2.0)


if __name__ == "__main__":
    unittest.main()
