"""
Data Loader & Preprocessing Module for Care Transition Efficiency & Placement Outcome Analytics.
Provides robust ingestion, data cleaning, date normalization, and derived feature engineering.
"""

import os
from typing import Tuple, Optional
import pandas as pd
import numpy as np


COLUMN_MAPPING = {
    'Date': 'Date',
    'Children apprehended and placed in CBP custody*': 'Apprehended',
    'Children apprehended and placed in CBP custody': 'Apprehended',
    'Children in CBP custody': 'CBP_Custody',
    'Children transferred out of CBP custody': 'CBP_Transfers',
    'Children in HHS Care': 'HHS_Care',
    'Children discharged from HHS Care': 'HHS_Discharges'
}

STANDARD_COLUMNS = [
    'Date', 'Apprehended', 'CBP_Custody', 'CBP_Transfers', 'HHS_Care', 'HHS_Discharges'
]


def load_raw_data(filepath: str) -> pd.DataFrame:
    """
    Load raw CSV dataset, sanitize column headers, strip commas, and drop blank rows.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found at: {filepath}")

    df = pd.read_csv(filepath)
    df = df.dropna(subset=['Date']).copy()

    # Normalize column names
    clean_cols = {}
    for col in df.columns:
        clean_name = col.replace('*', '').strip()
        matched = False
        for k, v in COLUMN_MAPPING.items():
            if k.replace('*', '').strip().lower() == clean_name.lower():
                clean_cols[col] = v
                matched = True
                break
        if not matched:
            clean_cols[col] = clean_name

    df = df.rename(columns=clean_cols)

    # Convert numeric fields
    numeric_cols = ['Apprehended', 'CBP_Custody', 'CBP_Transfers', 'HHS_Care', 'HHS_Discharges']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(',', '', regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    # Convert date
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date']).sort_values('Date').reset_index(drop=True)

    return df


def engineer_pipeline_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute derived transition efficiency, queueing, backlog, and stability metrics.
    """
    df = df.copy()

    # Time-based dimensions
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['Month_Name'] = df['Date'].dt.strftime('%b %Y')
    df['Day_Of_Week'] = df['Date'].dt.day_name()
    df['Day_Index'] = df['Date'].dt.dayofweek
    df['Is_Weekend'] = df['Day_Index'] >= 5
    df['Day_Type'] = np.where(df['Is_Weekend'], 'Weekend', 'Weekday')

    # Core Transition Efficiency Metrics
    # 1. Transfer Efficiency Ratio = Transfers ÷ CBP Custody
    df['Transfer_Efficiency_Ratio'] = np.where(
        df['CBP_Custody'] > 0,
        df['CBP_Transfers'] / df['CBP_Custody'],
        np.nan
    )

    # 2. Discharge Effectiveness = Discharges ÷ HHS Care
    df['Discharge_Effectiveness'] = np.where(
        df['HHS_Care'] > 0,
        df['HHS_Discharges'] / df['HHS_Care'],
        np.nan
    )

    # 3. Pipeline Throughput Rate = Total Exits (Discharges) ÷ Total Entries (Apprehensions)
    df['Pipeline_Throughput_Rate'] = np.where(
        df['Apprehended'] > 0,
        df['HHS_Discharges'] / df['Apprehended'],
        np.nan
    )

    # 4. Immediate Custodial Flow Balances (Daily Net Flow)
    df['CBP_Net_Change'] = df['Apprehended'] - df['CBP_Transfers']
    df['HHS_Net_Change'] = df['CBP_Transfers'] - df['HHS_Discharges']
    df['Total_System_Net_Change'] = df['Apprehended'] - df['HHS_Discharges']

    # 5. Cumulative Backlog / Intake-Exit Gap
    df['Cumulative_Inflow'] = df['Apprehended'].cumsum()
    df['Cumulative_Transfers'] = df['CBP_Transfers'].cumsum()
    df['Cumulative_Discharges'] = df['HHS_Discharges'].cumsum()
    df['Cumulative_System_Backlog'] = df['Cumulative_Inflow'] - df['Cumulative_Discharges']
    df['Cumulative_CBP_Backlog'] = df['Cumulative_Inflow'] - df['Cumulative_Transfers']
    df['Cumulative_HHS_Backlog'] = df['Cumulative_Transfers'] - df['Cumulative_Discharges']

    # 6. Queue Residence Time Proxies (Little's Law approximation in days)
    # Residence time W = L / lambda
    df['Est_CBP_Turnover_Days'] = np.where(
        df['CBP_Transfers'] > 0,
        df['CBP_Custody'] / df['CBP_Transfers'],
        np.nan
    )
    df['Est_HHS_Stay_Days'] = np.where(
        df['HHS_Discharges'] > 0,
        df['HHS_Care'] / df['HHS_Discharges'],
        np.nan
    )

    # 7. Rolling Moving Averages for Smoothing
    windows = [7, 14, 30]
    for w in windows:
        df[f'Transfer_Efficiency_MA{w}'] = (
            df['Transfer_Efficiency_Ratio'].rolling(window=w, min_periods=1).mean()
        )
        df[f'Discharge_Effectiveness_MA{w}'] = (
            df['Discharge_Effectiveness'].rolling(window=w, min_periods=1).mean()
        )
        df[f'Pipeline_Throughput_MA{w}'] = (
            df['Pipeline_Throughput_Rate'].rolling(window=w, min_periods=1).mean()
        )
        df[f'Discharges_MA{w}'] = (
            df['HHS_Discharges'].rolling(window=w, min_periods=1).mean()
        )
        df[f'Apprehended_MA{w}'] = (
            df['Apprehended'].rolling(window=w, min_periods=1).mean()
        )
        df[f'CBP_Custody_MA{w}'] = (
            df['CBP_Custody'].rolling(window=w, min_periods=1).mean()
        )
        df[f'HHS_Care_MA{w}'] = (
            df['HHS_Care'].rolling(window=w, min_periods=1).mean()
        )

    # 8. Outcome Stability Score (30-day Rolling)
    # Defined as 100 * (1 - normalized coefficient of variation)
    # Higher score = more stable and consistent reunification rate
    rolling_std_30 = df['HHS_Discharges'].rolling(30, min_periods=5).std()
    rolling_mean_30 = df['HHS_Discharges'].rolling(30, min_periods=5).mean()
    cv_30 = rolling_std_30 / (rolling_mean_30 + 1e-6)
    # Bound CV between 0 and 1 for 0-100 score
    df['Outcome_Stability_Score'] = (1.0 / (1.0 + cv_30)) * 100.0

    return df


def get_prepared_dataset(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Convenience function returning the fully engineered dataset.
    """
    if filepath is None:
        default_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "HHS_Unaccompanied_Alien_Children_Program.csv"
        )
        filepath = os.path.abspath(default_path)

    raw_df = load_raw_data(filepath)
    clean_df = engineer_pipeline_features(raw_df)
    return clean_df
