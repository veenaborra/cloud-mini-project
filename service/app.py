"""Command-parser service. Config: MODEL_URI, MODEL_VERSION, S3_ENDPOINT, MAX_NEW_TOKENS, FAULT_INJECT."""
import json, logging, os, socket, tempfile, threading, time

import boto3
import jsonschema
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import inference

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("service")

MODEL_URI = os.environ.get("MODEL_URI", "s3://models/v1/")
MODEL_VERSION = os.environ.get("MODEL_VERSION", "v1")
S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://localhost:8333")
MAX_NEW_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", "48"))
FAULT_INJECT = os.environ.get("FAULT_INJECT", "0") == "1"
POD_NAME = os.environ.get("POD_NAME") or socket.gethostname()
SCHEMA = jsonschema.Draft7Validator(json.load(open(os.environ.get("SCHEMA_PATH", "schema.json")))["json_schema"])

state = {"ready": False, "tok": None, "model": None}
lock = threading.Lock()          # one generation at a time (1 CPU per Pod)
app = FastAPI()


def load_model():
    bucket, _, prefix = MODEL_URI.removeprefix("s3://").partition("/")
    s3 = boto3.client("s3", endpoint_url=S3_ENDPOINT, region_name="us-east-1")
    while not state["ready"]:
        try:
            t0, dest = time.time(), tempfile.mkdtemp()
            log.info("MODEL DOWNLOAD START uri=%s version=%s", MODEL_URI, MODEL_VERSION)
            objs = s3.list_objects_v2(Bucket=bucket, Prefix=prefix).get("Contents", [])
            if not objs:
                raise RuntimeError(f"nothing under {MODEL_URI}")
            for o in objs:
                s3.download_file(bucket, o["Key"], os.path.join(dest, o["Key"][len(prefix):]))
            log.info("MODEL DOWNLOAD DONE files=%d seconds=%.1f", len(objs), time.time() - t0)
            tok, model = inference.load(dest, threads=1)
            inference.generate(tok, model, "warm up", 4)
            state.update(tok=tok, model=model, ready=True)
            log.info("MODEL READY version=%s total_seconds=%.1f", MODEL_VERSION, time.time() - t0)
        except Exception as e:
            log.error("model load failed, retrying: %s", e)
            time.sleep(5)


@app.on_event("startup")
def startup():
    threading.Thread(target=load_model, daemon=True).start()


def headers():
    return {"X-Model-Version": MODEL_VERSION, "X-Served-By": POD_NAME}


class Req(BaseModel):
    text: str


@app.post("/parse")
def parse(req: Req):
    if not state["ready"]:
        return JSONResponse({"error": "model_not_ready"}, 503, headers=headers())
    with lock:
        raw = inference.generate(state["tok"], state["model"], req.text, MAX_NEW_TOKENS)
    if FAULT_INJECT:
        raw = "not json"
    try:
        obj = json.loads(raw)
        if not SCHEMA.is_valid(obj):
            raise ValueError
    except ValueError:                               # JSONDecodeError is a ValueError too
        return JSONResponse({"error": "invalid_model_output"}, 500, headers=headers())
    return JSONResponse({k: obj[k] for k in ("intent", "date", "time", "place")}, 200, headers=headers())


@app.get("/healthz")
def healthz():
    return {"status": "alive"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"} if state["ready"] else JSONResponse({"status": "loading"}, 503)
