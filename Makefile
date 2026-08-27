PYTHON ?= python3

.PHONY: test validate catalog check

test:
	$(PYTHON) -m unittest discover -s tests -v

validate:
	$(PYTHON) scripts/validate_repository.py --root .
	$(PYTHON) scripts/check_skill_dependencies.py --root .

catalog:
	$(PYTHON) scripts/build_catalog.py --root .

check: test validate
	$(PYTHON) scripts/build_catalog.py --root . --check
