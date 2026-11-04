PY := .venv/bin/python
VERSION ?= v1
SUBSET ?= 0

train:   ## make train [VERSION=v2] [SUBSET=50]
	$(PY) training/train.py --version $(VERSION) $(if $(filter-out 0,$(SUBSET)),--subset $(SUBSET))

CLUSTER := cc-mini
S3ENV = set -a; . ./.s3.env; set +a;
.PHONY: train up down venv cluster storage images models deploy smoke

up: venv cluster storage images models deploy smoke

down:
	k3d cluster delete $(CLUSTER)

venv: .venv/.done
.venv/.done:
	python3 -m venv .venv
	.venv/bin/pip install -q -r requirements-ci.txt pyyaml==6.0.2
	touch $@

cluster:
	k3d cluster list $(CLUSTER) >/dev/null 2>&1 || k3d cluster create --config cluster/k3d.yaml

storage:
	scripts/make_secrets.sh
	kubectl apply -f k8s/data/seaweedfs.yaml
	kubectl -n data rollout status deploy/seaweedfs --timeout=300s
	until $(S3ENV) $(PY) scripts/s3_setup.py; do echo "waiting for S3..."; sleep 5; done

images:
	docker build -f service/Dockerfile -t cmd-parser:1.0 .
	docker build -f worker/Dockerfile -t cc-worker:1.0 .
	k3d image import cmd-parser:1.0 cc-worker:1.0 -c $(CLUSTER)

models:
	$(S3ENV) scripts/fetch_models.sh

deploy:
	kubectl apply -f k8s/app/app.yaml
	kubectl -n app rollout status deploy/cmd-parser --timeout=600s

smoke:
	sleep 5
	curl -si -X POST localhost:8080/parse -H 'Content-Type: application/json' -d '{"text":"set an alarm for seven am tomorrow"}'
