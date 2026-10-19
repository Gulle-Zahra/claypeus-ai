import pandas as pd
from datasets import load_dataset
from sklearn.model_selection import train_test_split

# 1. Load
df = load_dataset("MAlmasabi/Indirect-Prompt-Injection-BIPIA-GPT", split="train").to_pandas()
print("Loaded:", len(df))

# 2. Remove duplicates
df = df.drop_duplicates(subset=["user_intent", "context"]).reset_index(drop=True)
print("After removing duplicates:", len(df))

# 3. Map to our schema
out = pd.DataFrame({
    "id": [f"bipia_{i:05d}" for i in range(len(df))],
    "source_dataset": df["source"].map(lambda s: "BIPIA" if s == "BIPIA" else "BIPIA_GPT_benign"),
    "user_instruction": df["user_intent"],
    "external_content": df["context"],
    "label": df["label"].map({0: "clean", 1: "injected"}),
    "injection_span_text": "",
    "injection_start_char": pd.NA,
    "injection_end_char": pd.NA,
    "injection_category": "",
    "split": "",
})

# 4. Split 80/10/10, keeping the label balance equal in each part
train, temp = train_test_split(out, test_size=0.2, stratify=out["label"], random_state=42)
val, test = train_test_split(temp, test_size=0.5, stratify=temp["label"], random_state=42)
out.loc[train.index, "split"] = "train"
out.loc[val.index, "split"] = "val"
out.loc[test.index, "split"] = "test"

# 5. Save
out.to_csv("data/processed/zahra_bipia.csv", index=False)
print(pd.crosstab(out["split"], out["label"]))