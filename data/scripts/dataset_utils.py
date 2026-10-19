import os
from typing import Dict, List, Tuple

import pandas as pd

CANONICAL_COLUMNS = [
    "id",
    "source_dataset",
    "user_instruction",
    "external_content",
    "label",
    "injection_span_text",
    "injection_start_char",
    "injection_end_char",
    "injection_category",
    "split",
]

ALLOWED_LABELS = {"clean", "injected"}
ALLOWED_SPLITS = {"train", "val", "test"}
ALLOWED_INJECTION_CATEGORIES = {
    "instruction_override",
    "data_exfiltration",
    "tool_misuse",
    "other",
}

PREFIXES = {
    "injecagent": "injecagent_",
    "deepset": "deepset_",
    "hn": "hn_",
    "si": "si_",
}

def get_canonical_columns() -> List[str]:
    return list(CANONICAL_COLUMNS)


def _to_str(v):
    if pd.isna(v):
        return ""
    return str(v)


def _is_empty_str(v) -> bool:
    s = _to_str(v).strip()
    return s == ""


def validate_csv(path: str, strict_spans: bool = True) -> Dict:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    issues = []
    summary = {}

    # Column check
    if list(df.columns) != CANONICAL_COLUMNS:
        issues.append(
            f"Column order/name mismatch: expected {CANONICAL_COLUMNS}, got {list(df.columns)}"
        )

    # IDs
    ids = df["id"].apply(_to_str) if "id" in df else pd.Series([])
    empty_ids = ids[ids.str.strip() == ""].index.tolist()
    if empty_ids:
        issues.append(f"Empty IDs at rows: {empty_ids[:5]} (showing up to 5)")
    dup_ids = ids[ids.duplicated(keep=False)]
    if not dup_ids.empty:
        issues.append(f"Duplicate IDs: {dup_ids.unique().tolist()[:5]}")

    # Labels/splits/categories
    for idx, row in df.iterrows():
        label = _to_str(row.get("label", "")).strip()
        if label not in ALLOWED_LABELS:
            issues.append(f"Row {idx}: invalid label {label}")
        split = _to_str(row.get("split", "")).strip()
        if split not in ALLOWED_SPLITS:
            issues.append(f"Row {idx}: invalid split {split}")
        cat = _to_str(row.get("injection_category", "")).strip()
        if cat and cat not in ALLOWED_INJECTION_CATEGORIES:
            issues.append(f"Row {idx}: invalid injection_category {cat}")

        if label == "clean":
            span = _to_str(row.get("injection_span_text", "")).strip()
            s = _to_str(row.get("injection_start_char", "")).strip()
            e = _to_str(row.get("injection_end_char", "")).strip()
            catc = _to_str(row.get("injection_category", "")).strip()
            if span or s or e or catc:
                issues.append(f"Row {idx}: clean example must have empty injection metadata")

        if label == "injected":
            span = _to_str(row.get("injection_span_text", "")).strip()
            s_str = _to_str(row.get("injection_start_char", "")).strip()
            e_str = _to_str(row.get("injection_end_char", "")).strip()
            ext = _to_str(row.get("external_content", ""))
            if strict_spans and (s_str or e_str or span):
                if not s_str or not e_str:
                    issues.append(f"Row {idx}: injected must have both offsets if span/offsets given")
                    continue
                try:
                    s = int(s_str)
                    e = int(e_str)
                except ValueError:
                    issues.append(f"Row {idx}: non-integer offsets")
                    continue
                if s < 0 or e < 0 or e < s:
                    issues.append(f"Row {idx}: invalid offset range")
                    continue
                if e > len(ext):
                    issues.append(f"Row {idx}: end offset {e} > len(content) {len(ext)}")
                    continue
                if span and ext[s:e] != span:
                    issues.append(f"Row {idx}: span mismatch ext[{s}:{e}]!={span!r}")
            # if no spans provided, that's allowed only if documented; we don't reject

    summary["n_rows"] = len(df)
    summary["labels"] = df["label"].value_counts().to_dict() if "label" in df else {}
    summary["splits"] = df["split"].value_counts().to_dict() if "split" in df else {}
    summary["valid"] = len(issues) == 0
    return {"issues": issues, "summary": summary}


def save_processed_csv(df: pd.DataFrame, out_path: str) -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df = df.reindex(columns=CANONICAL_COLUMNS)
    df.to_csv(out_path, index=False, encoding="utf-8")
    return out_path


def validate_spans_against_content(df: pd.DataFrame) -> List[str]:
    issues = []
    for idx, row in df.iterrows():
        if _to_str(row.get("label", "")).strip() == "clean":
            continue
        s_str = _to_str(row.get("injection_start_char", "")).strip()
        e_str = _to_str(row.get("injection_end_char", "")).strip()
        span = _to_str(row.get("injection_span_text", "")).strip()
        if not (s_str and e_str):
            continue
        try:
            s, e = int(s_str), int(e_str)
        except ValueError:
            issues.append(f"Row {idx}: bad offsets")
            continue
        ext = _to_str(row.get("external_content", ""))
        if s < 0 or e > len(ext) or e < s:
            issues.append(f"Row {idx}: bad range")
            continue
        if span and ext[s:e] != span:
            issues.append(f"Row {idx}: span mismatch")
    return issues
