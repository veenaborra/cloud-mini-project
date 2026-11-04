"""Run a model on validation.jsonl, write {"id","prediction"} lines for score.py.

  python training/predict.py <model dir or HF id> <output.jsonl>
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "service"))
from inference import generate, load  # noqa: E402

model_path, out = sys.argv[1], sys.argv[2]
tok, model = load(model_path)
rows = [json.loads(line) for line in open("data/validation.jsonl", encoding="utf-8") if line.strip()]
with open(out, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps({"id": r["id"], "prediction": generate(tok, model, r["text"])}) + "\n")
print("wrote", out)
