"""Clean teacher shards into a training set (Task 1.6).

  python worker/clean.py data/teacher/ data/train/ [--pool data/commands_pool.jsonl]

Removes, in this order (first failing reason counts):
  (a) invalid_json   reply is not a JSON object
  (b) wrong_keys     keys are not exactly intent, date, time, place
  (c) bad_intent     intent not one of the eight
  (d) invented_slot  a slot is neither null nor non-empty text that appears in the command
  (e) duplicate      same command text as a kept record with a smaller id
Writes train.jsonl (sorted by id) and train.sha256.
"""
import argparse
import hashlib
import json
import os

KEYS = ["intent", "date", "time", "place"]
INTENTS = {"alarm_set", "alarm_query", "calendar_set", "calendar_query",
           "calendar_remove", "weather_query", "datetime_query", "recommendation_events"}


def norm(s):
    return " ".join(s.lower().split())


def check(text, raw):
    """Return (reason, parsed). reason is None if the record is good."""
    try:
        obj = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return "invalid_json", None
    if not isinstance(obj, dict):
        return "invalid_json", None
    if set(obj) != set(KEYS):
        return "wrong_keys", None
    if obj["intent"] not in INTENTS:
        return "bad_intent", None
    for k in ("date", "time", "place"):
        v = obj[k]
        if v is not None and (not isinstance(v, str) or not v.strip() or norm(v) not in norm(text)):
            return "invented_slot", None
    return None, obj


def clean(records):
    counts = {"input": len(records), "invalid_json": 0, "wrong_keys": 0, "bad_intent": 0,
              "invented_slot": 0, "duplicate": 0, "kept": 0}
    passed = []
    for r in sorted(records, key=lambda r: r["id"]):
        reason, obj = check(r["text"], r["teacher_raw"])
        if reason:
            counts[reason] += 1
        else:
            # target = same values, fixed key order and spacing (teacher_raw kept untouched)
            target = json.dumps({k: obj[k] for k in KEYS}, ensure_ascii=False)
            passed.append({"id": r["id"], "text": r["text"], "teacher_raw": r["teacher_raw"], "target": target})
    seen, kept = set(), []
    for r in passed:                      # sorted by id, so the smallest id wins
        key = norm(r["text"])
        if key in seen:
            counts["duplicate"] += 1
        else:
            seen.add(key)
            kept.append(r)
    counts["kept"] = len(kept)
    assert counts["input"] == sum(v for k, v in counts.items() if k != "input")
    return kept, counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--pool", help="check every pool id appears in exactly one shard")
    a = ap.parse_args()

    records, owner = [], {}
    for name in sorted(os.listdir(a.src)):
        if name.endswith(".jsonl"):
            for line in open(os.path.join(a.src, name), encoding="utf-8"):
                if line.strip():
                    r = json.loads(line)
                    records.append(r)
                    owner.setdefault(r["id"], []).append(name)
    if a.pool:
        pool = [json.loads(l)["id"] for l in open(a.pool) if l.strip()]
        missing = [i for i in pool if i not in owner]
        repeated = [i for i, s in owner.items() if len(s) > 1]
        print(f"coverage: {len(pool)} pool ids, missing={len(missing)}, repeated={len(repeated)}")

    kept, counts = clean(records)
    body = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept).encode("utf-8")
    digest = hashlib.sha256(body).hexdigest()
    os.makedirs(a.dst, exist_ok=True)
    open(os.path.join(a.dst, "train.jsonl"), "wb").write(body)
    open(os.path.join(a.dst, "train.sha256"), "w").write(f"{digest}  train.jsonl\n")
    print(json.dumps(counts, indent=2))
    print("sha256", digest)


if __name__ == "__main__":
    main()
