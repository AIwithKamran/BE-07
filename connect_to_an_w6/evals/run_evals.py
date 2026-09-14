import json
import requests
from pathlib import Path

CASES_FILE = Path("evals/cases.json")
ENDPOINT = "http://127.0.0.1:8000/triage"

def main():
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    passed = 0
    total = len(cases)
    failures = []

    for c in cases:
        resp = requests.post(ENDPOINT, json={"text": c["text"]})
        if resp.status_code != 200:
            failures.append((c["id"], f"HTTP {resp.status_code}: {resp.text}"))
            continue
        data = resp.json()
        if data.get("category") == c["expected_category"]:
            passed += 1
        else:
            failures.append((c["id"], f"Expected {c['expected_category']}, got {data.get('category')}"))

    print(f"\n--- EVALUATION RESULT ---")
    print(f"Score: {passed}/{total} ({(passed/total)*100:.1f}%)")
    if failures:
        print("Mismatches:")
        for cid, msg in failures:
            print(f" - Case {cid}: {msg}")

if __name__ == "__main__":
    main()