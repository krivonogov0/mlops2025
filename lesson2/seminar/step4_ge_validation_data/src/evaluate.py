import json
import pickle
from pathlib import Path

import pandas as pd
import yaml
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


def load_params():
    with Path("params.yaml").open() as f:
        return yaml.safe_load(f)


def evaluate_model():
    params = load_params()

    with Path("models/model.pkl").open("rb") as f:
        model = pickle.load(f)

    df = pd.read_csv("data/processed/dataset.csv")

    X = df[["total_bill", "size"]]
    y = df["high_tip"]

    _, X_test, _, y_test = train_test_split(
        X,
        y,
        test_size=params["test_size"],
        random_state=params["seed"],
    )

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    n_rows = len(X_test)

    # Save metrics: accuracy, length
    metrics = {
        "accuracy": float(accuracy),
        "n_rows": n_rows,
    }
    metrics_dir = Path("metrics")
    metrics_dir.mkdir(exist_ok=True)
    with (metrics_dir / "metrics.json").open("w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Accuracy: {accuracy:.4f}")
    print(f"Test samples: {n_rows}")


if __name__ == "__main__":
    evaluate_model()
