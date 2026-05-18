import os
import pandas as pd
import streamlit as st

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(_PROJECT_ROOT, 'data', 'mtbs_ca_summary.csv')
SAMPLE_DATA_PATH = os.path.join(_PROJECT_ROOT, 'data', 'mtbs_ca_summary_sample.csv')


@st.cache_data
def load_data() -> pd.DataFrame:
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    if os.path.exists(SAMPLE_DATA_PATH):
        return pd.read_csv(SAMPLE_DATA_PATH)
    return pd.DataFrame()


def is_sample_data() -> bool:
    """True when running on the committed sample CSV rather than the full dataset."""
    return not os.path.exists(DATA_PATH) and os.path.exists(SAMPLE_DATA_PATH)
