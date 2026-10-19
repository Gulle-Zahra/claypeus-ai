#!/usr/bin/env python3
import os
import sys
import random

import pandas as pd
from datasets import load_dataset

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from data.scripts import dataset_utils

CANONICAL = dataset_utils.CANONICAL_COLUMNS
GENERIC_USER_INSTR = "Classify whether the following text contains a prompt injection."


def main():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "processed")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "usman_deepset.csv")

    print("Loading deepset/prompt-injections from HF...")
    ds = load_dataset("deepset/prompt-injections")
    all_items = []
    for k in ds:
        for i, ex in enumerate(ds[k]):
            all_items.append(ex)

    random.seed(42)
    random.shuffle(all_items)
    n = len(all_items)
    train_n = int(n * 0.8)
    val_n = int(n * 0.1)
    splits = ["train"] * train_n + ["val"] * val_n + ["test"] * (n - train_n - val_n)

    rows = []
    for idx, (ex, split) in enumerate(zip(all_items, splits)):
        text = ex.get("text", "") or ""
        label_src = ex.get("label", "")
        if label_src == 0 or label_src == "0":
            label = "clean"
        elif label_src == 1 or label_src == "1":
            label = "injected"
        else:
            print(f"Skipping unknown label: {label_src}")
            continue
        injection_category = "instruction_override" if label == "injected" else ""
        rows.append(
            {
                "id": f"deepset_{idx+1:05d}",
                "source_dataset": "deepset",
                "user_instruction": GENERIC_USER_INSTR,
                "external_content": text,
                "label": label,
                "injection_span_text": "",
                "injection_start_char": "",
                "injection_end_char": "",
                "injection_category": injection_category,
                "split": split,
            }
        )

    df = pd.DataFrame(rows, columns=CANONICAL)
    dataset_utils.save_processed_csv(df, out_path)
    print(f"Wrote {len(df)} rows to {out_path}")
    print(df["label"].value_counts().to_dict())
    print(df["split"].value_counts().to_dict())
    res = dataset_utils.validate_csv(out_path)
    print("valid:", res["summary"]["valid"], res["issues"][:3])


if __name__ == "__main__":
    main()
