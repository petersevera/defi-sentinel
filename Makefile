PYTHON ?= python

.PHONY: setup-core setup-rag validate ingest-rss ingest-onchain features rag-index rag-query api

setup-core:
	$(PYTHON) -m pip install -r requirements-core.txt

setup-rag:
	$(PYTHON) -m pip install -r requirements-rag.txt

validate:
	$(PYTHON) scripts/validate_fixtures.py

ingest-rss:
	$(PYTHON) scripts/ingest_rss.py

ingest-onchain:
	$(PYTHON) scripts/ingest_onchain.py

features:
	$(PYTHON) scripts/build_features.py

rag-index:
	$(PYTHON) scripts/build_rag_index.py

rag-query:
	$(PYTHON) scripts/query_rag.py "aave governance risk parameters"

api:
	$(PYTHON) scripts/run_api.py
