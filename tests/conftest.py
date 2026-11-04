import os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
for sub in ("worker", "service", "tools"):
    sys.path.insert(0, os.path.join(ROOT, sub))
os.environ.setdefault("SCHEMA_PATH", os.path.join(ROOT, "data", "schema.json"))
