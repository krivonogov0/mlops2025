import json
import sys
from pathlib import Path

import yaml


def load_params():
    with Path("params.yaml").open() as f:
        return yaml.safe_load(f)


def validate_model():
    params = load_params()

    # Get accuracy limit
    accuracy_min = params.get("accuracy_min")
    if accuracy_min is None:
        print("Error: 'accuracy_min' not found in params.yaml", file=sys.stderr)
        sys.exit(1)

    # Read metrics
    metrics_path = Path("metrics/metrics.json")
    with metrics_path.open() as f:
        metrics = json.load(f)

    accuracy = metrics.get("accuracy")
    if accuracy is None:
        print("Error: 'accuracy' not found in metrics/metrics.json", file=sys.stderr)
        sys.exit(1)

    # Compare with accuracy limit
    if accuracy < accuracy_min:
        print(
            f"Model validation FAILED: accuracy = {accuracy:.4f} < threshold = {accuracy_min}",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print(
            f"Model validation PASSED: accuracy = {accuracy:.4f} >= threshold = {accuracy_min}"
        )


if __name__ == "__main__":
    validate_model()
