import json
import requests
import pandas as pd

BASE = "https://raw.githubusercontent.com/microsoft/BIPIA/main/benchmark/"
FILES = ["text_attack_train.json", "text_attack_test.json",
         "code_attack_train.json", "code_attack_test.json"]

# 1. Collect every attack sentence and its category
attacks = []
def collect(obj, key=None):
    if isinstance(obj, dict):
        for k, v in obj.items():
            collect(v, k)
    elif isinstance(obj, list):
        for v in obj:
            collect(v, key)
    elif isinstance(obj, str) and obj.strip():
        attacks.append((obj.strip(), key))

for f in FILES:
    r = requests.get(BASE + f)
    r.raise_for_status()
    collect(r.json())

attacks = list(set(attacks))
attacks.sort(key=lambda a: len(a[0]), reverse=True)   # try the longest first
print("Attack sentences collected:", len(attacks))

# 2. Search for them in the injected rows

df = pd.read_csv("data/processed/zahra_bipia.csv", keep_default_na=False)

# Number columns: empty cells become missing values, numbers stay numbers
for col in ["injection_start_char", "injection_end_char"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

# Text columns: make sure they accept strings
for col in ["injection_span_text", "injection_category"]:
    df[col] = df[col].astype("object")
injected = df.index[df["label"] == "injected"]

found = 0
for n, i in enumerate(injected):
    text = df.at[i, "external_content"]
    for attack, category in attacks:
        pos = text.find(attack)
        if pos >= 0:
            df.at[i, "injection_span_text"] = attack
            df.at[i, "injection_start_char"] = pos
            df.at[i, "injection_end_char"] = pos + len(attack)
            df.at[i, "injection_category"] = category or ""
            found += 1
            break
    if n % 5000 == 0:
        print(f"Checked {n} / {len(injected)}")

print(f"Spans found for {found} of {len(injected)} injected rows ({found/len(injected):.1%})")
df.to_csv("data/processed/zahra_bipia.csv", index=False)