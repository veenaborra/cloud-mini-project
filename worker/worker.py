"""Labelling worker: asks the teacher about its shard of commands_pool.jsonl.

Env: SHARD_INDEX, SHARD_COUNT, OLLAMA_URL, S3_ENDPOINT, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
Line i (from 0) belongs to this worker if i % SHARD_COUNT == SHARD_INDEX.
Writes {"id","text","teacher_raw"} lines to datasets/teacher/shard-<SHARD_INDEX>.jsonl.
"""
import json
import os
import time
import urllib.request

import boto3

SHARD_INDEX = int(os.environ["SHARD_INDEX"])
SHARD_COUNT = int(os.environ["SHARD_COUNT"])
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434")
BUCKET = "datasets"
OUT_KEY = f"teacher/shard-{SHARD_INDEX}.jsonl"
FLUSH_EVERY = 25

s3 = boto3.client("s3", endpoint_url=os.environ["S3_ENDPOINT"], region_name="us-east-1")
template = open(os.environ.get("PROMPT_PATH", "/app/prompts/teacher_prompt.txt")).read()


def ask_teacher(command):
    body = {"model": "phi3.5", "prompt": template.replace("{command}", command), "stream": False,
            "format": "json", "options": {"temperature": 0, "seed": 42}, "keep_alive": "30m"}
    for attempt in range(3):
        try:
            req = urllib.request.Request(f"{OLLAMA_URL}/api/generate", json.dumps(body).encode(),
                                         {"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())["response"]  # stored exactly as generated
        except Exception as e:
            print(f"retry {attempt + 1}: {e}", flush=True)
            time.sleep(5)
    raise RuntimeError("teacher unreachable")


def save(lines):
    s3.put_object(Bucket=BUCKET, Key=OUT_KEY, Body=("\n".join(lines) + "\n").encode())


lines = s3.get_object(Bucket=BUCKET, Key="commands_pool.jsonl")["Body"].read().decode().splitlines()
mine = [json.loads(l) for i, l in enumerate(lines) if l.strip() and i % SHARD_COUNT == SHARD_INDEX]
print(f"shard {SHARD_INDEX}/{SHARD_COUNT}: {len(mine)} commands -> {BUCKET}/{OUT_KEY}", flush=True)

# resume: keep what an earlier run already saved
try:
    done = s3.get_object(Bucket=BUCKET, Key=OUT_KEY)["Body"].read().decode().splitlines()
    done = [l for l in done if l.strip()]
except s3.exceptions.NoSuchKey:
    done = []
done_ids = {json.loads(l)["id"] for l in done}
print(f"already done: {len(done_ids)}", flush=True)

t0, new = time.time(), 0
for rec in mine:
    if rec["id"] in done_ids:
        continue
    raw = ask_teacher(rec["text"])
    done.append(json.dumps({"id": rec["id"], "text": rec["text"], "teacher_raw": raw}, ensure_ascii=False))
    new += 1
    if new % FLUSH_EVERY == 0:
        save(done)
        rate = new / (time.time() - t0)
        print(f"{len(done)}/{len(mine)}  {rate:.2f} cmd/s  ~{(len(mine) - len(done)) / rate / 60:.0f} min left",
              flush=True)
save(done)
print(f"finished shard {SHARD_INDEX}: {len(done)} records", flush=True)
