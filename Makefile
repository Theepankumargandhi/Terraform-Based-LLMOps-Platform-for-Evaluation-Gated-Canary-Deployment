PYTHON ?= python

.PHONY: install test eval run terraform-fmt

install:
	$(PYTHON) -m pip install -e .[dev]

test:
	$(PYTHON) -m pytest

eval:
	$(PYTHON) -m scripts.run_evaluation --stable configs/releases/stable.yaml --candidate configs/releases/candidate.yaml --dataset data/evals/incidents.jsonl --output artifacts/evaluations/latest.json

run:
	$(PYTHON) -m llmops_platform.main

terraform-fmt:
	terraform fmt -recursive infra
