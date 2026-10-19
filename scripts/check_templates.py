import json

BANNED = ["ignore", "previous instructions", "system prompt", "disregard", "override", "jailbreak"]
t = json.load(open("templates/subtle_injections.json"))

problems = 0
for s in t["styles"]:
    for v in s["variants"]:
        text = " ".join(v.values()) if isinstance(v, dict) else v
        for word in BANNED:
            if word in text.lower():
                print(f"[{s['style']}] uses banned word '{word}': {text}")
                problems += 1
        if "{goal}" not in text:
            print(f"[{s['style']}] missing {{goal}}: {text}")
            problems += 1

print("All templates OK" if problems == 0 else f"{problems} problems found")