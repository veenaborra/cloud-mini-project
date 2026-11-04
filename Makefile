PY := .venv/bin/python
VERSION ?= v1
SUBSET ?= 0

train:   ## make train [VERSION=v2] [SUBSET=50]
	$(PY) training/train.py --version $(VERSION) $(if $(filter-out 0,$(SUBSET)),--subset $(SUBSET))
