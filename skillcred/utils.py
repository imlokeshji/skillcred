
import pandas as pd
import random

def assign_segment_from_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if 'Segment' not in df.columns:
        df['Segment'] = 'New'
    return df

def generate_discount_code(segment: str) -> str:
    return f"{segment[:3].upper()}{random.randint(1000,9999)}"

def segment_to_discount(segment: str, rules: dict) -> str:
    pct = rules.get(segment, rules.get('Default', 10))
    return f"{pct}%"
