# Cloud Computing Mini Project: distilled command parser on k3d

Pythia-70M fine-tuned on phi3.5 replies (sequence-level knowledge distillation), served with FastAPI
on a local k3d cluster, with SeaweedFS object storage.

## Requirements
Docker, k3d v5, kubectl, Python 3.11+, make, git, curl. Ollama + phi3.5 only for labelling.

## Build and deploy (fresh clone)
    git clone https://github.com/veenaborra/cloud-mini-project.git && cd cloud-mini-project
    make up        # venv, cluster, SeaweedFS + buckets, images, models from Releases, deploy, smoke test
    make down      # delete the cluster

Service: `curl -X POST localhost:8080/parse -H 'Content-Type: application/json' -d '{"text":"what time is it"}'`

## Pipeline
| Step | Command |
|---|---|
| Teacher labelling (2 parallel workers) | `kubectl apply -f k8s/pipeline/label-job.yaml` |
| Clean shards | `python worker/clean.py data/teacher/ data/train/ --pool data/commands_pool.jsonl` |
| Train (quick check / full) | `make train SUBSET=50`, `make train VERSION=v1`, `make train VERSION=v2` |
| Package + upload + checksum | `python training/package.py v1` |
| Evaluate | `python training/predict.py build/model-v1 results/student_v1_predictions.jsonl` then `python tools/score.py ...` |

## Test
    pytest -q tests && ruff check .
    locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 2m --host http://localhost:8080 --csv results/loadtest
    python tools/nacl_sim.py network/nacl.json network/packets_sample.jsonl --check

Credentials are generated into the git-ignored `.s3.env` and Kubernetes Secrets by `scripts/make_secrets.sh`.
Evidence for every task is in `results/`.
