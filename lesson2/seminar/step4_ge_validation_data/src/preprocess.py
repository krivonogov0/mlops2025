from pathlib import Path

import pandas as pd

TIPS_THRESHOLD = 0.2


def preprocess_data():
    df = pd.read_csv("data/raw/tips.csv")

    df["high_tip"] = (df["tip"] / df["total_bill"]) > TIPS_THRESHOLD

    processed_df = df[["total_bill", "size", "high_tip"]].copy()

    processed_data_dir = Path("data/processed")
    processed_data_dir.mkdir(parents=True, exist_ok=True)
    processed_df.to_csv("data/processed/dataset.csv", index=False)


if __name__ == "__main__":
    preprocess_data()
