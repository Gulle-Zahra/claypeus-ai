#!/usr/bin/env python3
import os
import sys
import json
import random
import urllib.request

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from data.scripts import dataset_utils

CANONICAL = dataset_utils.CANONICAL_COLUMNS


def load_remote_json(url):
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"Failed to load {url}: {e}")
        return None


def map_attack_category(attack_type, attacker_instr):
    if not attacker_instr:
        return ""
    at = str(attack_type).lower()
    if "exfil" in at:
        return "data_exfiltration"
    if "tool" in at and "misuse" in at:
        return "tool_misuse"
    if "override" in at or "instruction" in at:
        return "instruction_override"
    return "instruction_override"


def main():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "processed")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "usman_injecagent.csv")

    all_items = []
    # try known remote files
    urls = [
        "https://raw.githubusercontent.com/uiuc-kang-lab/InjecAgent/main/data/test_cases_ds_base.json",
        "https://raw.githubusercontent.com/uiuc-kang-lab/InjecAgent/main/data/test_cases_dh_base.json",
    ]
    for url in urls:
        data = load_remote_json(url)
        if isinstance(data, list) and data:
            all_items.extend(data)
            print(f"Loaded {len(data)} from {url}")
    if not all_items:
        # fallback to local
        raw = os.path.join(os.path.dirname(__file__), "..", "raw")
        for name in os.listdir(raw) if os.path.exists(raw) else []:
            if name.endswith(".json"):
                try:
                    with open(os.path.join(raw, name), "r", encoding="utf-8") as f:
                        d = json.load(f)
                        if isinstance(d, list):
                            all_items.extend(d)
                except Exception:
                    pass

    if not all_items:
        print("No InjecAgent source found; writing empty CSV.")
        df = pd.DataFrame(columns=CANONICAL)
        dataset_utils.save_processed_csv(df, out_path)
        return

    random.seed(42)
    random.shuffle(all_items)
    n = len(all_items)
    train_n = int(n * 0.8)
    val_n = int(n * 0.1)
    splits = ["train"] * train_n + ["val"] * val_n + ["test"] * (n - train_n - val_n)

    rows = []
    for idx, (ex, split) in enumerate(zip(all_items, splits)):
        user_instr = ex.get("User Instruction") or ex.get("user_instruction") or ex.get("instruction") or ""
        tool_resp = ex.get("Tool Response Template") or ex.get("Tool Response") or ex.get("tool_output") or ex.get("tool_response") or ""
        attacker_instr = ex.get("Attacker Instruction") or ex.get("attacker_instruction") or ex.get("malicious_instruction") or ""
        external_content = tool_resp
        if attacker_instr:
            sep = "\n\n" if external_content and not str(external_content).endswith("\n") else ""
            external_content = f"{external_content}{sep}{attacker_instr}" if external_content else attacker_instr
        attack_type = ex.get("Attack Type") or ex.get("attack_type") or ""
        if attacker_instr:
            label = "injected"
            cat = map_attack_category(attack_type, attacker_instr)
        else:
            label = "clean"
            cat = ""
        span = attacker_instr if label == "injected" else ""
        s = e = ""
        if label == "injected" and span and str(span) in str(external_content):
            s = str(external_content).index(str(span))
            e = s + len(str(span))
        rows.append(
            {
                "id": f"injecagent_{idx+1:05d}",
                "source_dataset": "injecagent",
                "user_instruction": str(user_instr),
                "external_content": str(external_content),
                "label": label,
                "injection_span_text": str(span) if span else "",
                "injection_start_char": str(s) if s != "" else "",
                "injection_end_char": str(e) if e != "" else "",
                "injection_category": cat,
                "split": split,
            }
        )

    df = pd.DataFrame(rows, columns=CANONICAL)
    dataset_utils.save_processed_csv(df, out_path)
    print(f"Wrote {len(df)} rows to {out_path}")
    res = dataset_utils.validate_csv(out_path)
    print(res["summary"], res["issues"][:3])


if __name__ == "__main__":
    main()
