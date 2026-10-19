import json, random
import pandas as pd

random.seed(42)
t = json.load(open("templates/subtle_injections.json"))
d = pd.read_csv("data/processed/zahra_bipia.csv", keep_default_na=False)
docs = d[d["label"] == "clean"]["external_content"].sample(20, random_state=42).tolist()

def insert(doc, text, position):
    if position == "start":
        return text + " " + doc
    if position == "end":
        return doc + " " + text
    # middle: insert at the sentence break closest to the middle
    mid = len(doc) // 2
    cut = doc.find(". ", mid)
    cut = mid if cut == -1 else cut + 2
    return doc[:cut] + text + " " + doc[cut:]

for s in t["styles"]:
    goal = random.choice(t["goals"])["text"]
    v = random.choice(s["variants"])
    doc = random.choice(docs)[:600]
    if isinstance(v, dict):
        result = v["part1"] + " " + doc + " " + v["part2"].format(goal=goal)
        pos = "split"
    else:
        pos = random.choice(t["positions"])
        result = insert(doc, v.format(goal=goal), pos)
    print(f"=== {s['style']} ({pos}) ===\n{result}\n")