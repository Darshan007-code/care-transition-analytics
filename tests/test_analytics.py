"""
Unit Tests for Care Transition Efficiency & Placement Outcome Analytics Pipeline.
Validates mathematical consistency, Little's Law relationships, and anomaly detections.
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_loader import get_prepared_dataset, load_raw_data
from src.pipeline_metrics import (
    compute_executive_kpis,
    analyze_day_of_week_dynamics,
    analyze_monthly_trends,
    generate_sankey_data,
    detect_bottleneck_episodes
)
from src.anomaly_detector import detect_discharge_anomalies, get_active_alerts_summary
from src.scenario_simulator import run_pipeline_simulation


class TestCareTransitionAnalytics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "HHS_Unaccompanied_Alien_Children_Program.csv"))
        cls.df = get_prepared_dataset(cls.data_path)

    def test_data_ingestion(self):
        """Test dataset shape, column completeness, and absence of NaN in core fields."""
        self.assertGreater(len(self.df), 700, "Dataset should have at least 700 valid records")
        expected_cols = ['Date', 'Apprehended', 'CBP_Custody', 'CBP_Transfers', 'HHS_Care', 'HHS_Discharges']
        for col in expected_cols:
            self.assertIn(col, self.df.columns, f"Missing critical column: {col}")
            self.assertEqual(self.df[col].isna().sum(), 0, f"Column {col} has unexpected nulls")

    def test_derived_metrics_validity(self):
        """Verify mathematical definitions of transfer efficiency and discharge effectiveness."""
        # Non-negative checks
        self.assertTrue((self.df['Apprehended'] >= 0).all())
        self.assertTrue((self.df['CBP_Custody'] >= 0).all())
        self.assertTrue((self.df['CBP_Transfers'] >= 0).all())
        self.assertTrue((self.df['HHS_Care'] >= 0).all())
        self.assertTrue((self.df['HHS_Discharges'] >= 0).all())

        # Transfer Efficiency should be positive
        valid_trans_eff = self.df['Transfer_Efficiency_Ratio'].dropna()
        self.assertTrue((valid_trans_eff >= 0).all())

        # Discharge effectiveness should be positive and bounded (< 1.0)
        valid_disc_eff = self.df['Discharge_Effectiveness'].dropna()
        self.assertTrue((valid_disc_eff >= 0).all())
        self.assertTrue((valid_disc_eff <= 1.0).all())

    def test_executive_kpis_calculation(self):
        """Verify executive KPI scorecard computation."""
        kpis = compute_executive_kpis(self.df)
        self.assertIn('mean_transfer_efficiency', kpis)
        self.assertIn('mean_discharge_effectiveness', kpis)
        self.assertIn('global_throughput', kpis)
        self.assertIn('tvpra_compliance_pct', kpis)

        # Check reasonable bounds
        self.assertGreater(kpis['mean_transfer_efficiency'], 0.4)
        self.assertLess(kpis['mean_transfer_efficiency'], 1.5)
        self.assertGreater(kpis['tvpra_compliance_pct'], 70.0)

    def test_littles_law_residence_times(self):
        """Verify queue residence time bounds according to Little's law."""
        kpis = compute_executive_kpis(self.df)
        # CBP residence time should be around 1 to 3 days (TVPRA limit is 3 days)
        self.assertGreater(kpis['avg_cbp_residence_days'], 0.5)
        self.assertLess(kpis['avg_cbp_residence_days'], 4.0)

        # HHS stay should be around 20 to 60 days
        self.assertGreater(kpis['avg_hhs_residence_days'], 15.0)
        self.assertLess(kpis['avg_hhs_residence_days'], 60.0)

    def test_sankey_data_structure(self):
        """Ensure Sankey flow dictionary conforms to Plotly graph specifications."""
        sankey = generate_sankey_data(self.df)
        self.assertIn('labels', sankey)
        self.assertIn('sources', sankey)
        self.assertIn('targets', sankey)
        self.assertIn('values', sankey)
        self.assertEqual(len(sankey['sources']), len(sankey['targets']))
        self.assertEqual(len(sankey['sources']), len(sankey['values']))

    def test_anomaly_detection(self):
        """Check anomaly detection flags and summary generation."""
        anom_df = detect_discharge_anomalies(self.df)
        self.assertIn('ML_Anomaly', anom_df.columns)
        self.assertIn('Alert_Severity', anom_df.columns)
        alerts = get_active_alerts_summary(anom_df)
        self.assertGreater(alerts['high_severity_count'] + alerts['medium_severity_count'], 0)

    def test_scenario_simulator(self):
        """Check discrete simulation engine under stress scenarios."""
        sim = run_pipeline_simulation(self.df, days_horizon=30, intake_multiplier=1.2)
        self.assertEqual(len(sim), 30)
        self.assertTrue((sim['Simulated_CBP_Custody'] >= 0).all())
        self.assertTrue((sim['Simulated_HHS_Care'] >= 0).all())


if __name__ == '__main__':
    unittest.main()
