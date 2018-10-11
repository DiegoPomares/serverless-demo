REQS := requirements.txt
PY_DIR := ../../.venvpython/bin

SOURCE := ./code
TARGET := ./dist
REPORTS := ./reports
PYTHON := PATH="$(PY_DIR):$(PATH)" PYTHONPATH="$(TARGET)" $(PY_DIR)/python
PIP := PATH="$(PY_DIR):$(PATH)" PYTHONPATH="$(TARGET)" $(PY_DIR)/pip

SHELL := bash

.PHONY: dist
dist: | bootstrap delete-garbage


.PHONY: test
test: | bootstrap pytest delete-garbage


.PHONY: clean
clean: delete-garbage
	@ rm -rf $(TARGET)
	@ rm -rf $(REPORTS)


.PHONY: delete-garbage
delete-garbage:
	@ rm -f .coverage
	@ rm -rf .pytest_cache
	@ find . -type f -name "*.py[cod]" -delete
	@ find . -type d -name "__pycache__" -exec rm -rf "{}" +


.PHONY: bootstrap
bootstrap:
ifeq ("$(wildcard $(TARGET))", "")

	@ cp -rf $(SOURCE) $(TARGET)

ifneq ("$(wildcard $(REQS))", "")
	$(PIP) install -U -t $(TARGET) -r $(REQS) | grep -i 'installed'
endif

endif


.PHONY: pytest
pytest:
	$(PYTHON) ../../helpers/run_pytest.py $(ARGS)
