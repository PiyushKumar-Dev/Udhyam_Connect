from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ml.features import extract_features

BASE_DIR = Path(__file__).resolve().parent.parent


def main() -> None:
    decisions_file = BASE_DIR / "data" / "review_training_export.json"
    if not decisions_file.exists():
        print("No review training export found. Seed and export decisions first.")
        return

    records = json.loads(decisions_file.read_text(encoding="utf-8"))
    frame = pd.DataFrame(
        [
            {
                **extract_features(record["evidence"]),
                "label": 1 if record["decision"] == "APPROVE" else 0,
            }
            for record in records
        ]
    )
    print(frame.describe(include="all"))


if __name__ == "__main__":
    main()
