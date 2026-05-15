import pandas as pd

def load_and_clean(filepath):
    df = pd.read_csv(filepath)
    # Drop rows with missing values
    df = df.dropna()
    # Convert yes/no columns to 1/0
    for col in ["has_internet", "has_phone", "churned"]:
        if df[col].dtype == object:
            df[col] = df[col].map({"Yes": 1, "No": 0})
    # Fix total_charges if loaded as string
    df["total_charges"] = pd.to_numeric(df["total_charges"], errors="coerce").fillna(0.0)
    return df

def get_feature_stats(df):
    return df.describe().to_dict()
