INSTALL_STAMP := .install.stamp
POETRY := $(shell command -v poetry 2> /dev/null)

.DEFAULT_GOAL:=help

install: $(INSTALL_STAMP)
$(INSTALL_STAMP): pyproject.toml poetry.lock
	@if [ -z $(POETRY) ]; then echo "Poetry could not be found. See https://python-poetry.org/docs/"; exit 2; fi
	$(POETRY) install
	touch $(INSTALL_STAMP)

.PHONY: test
test: $(INSTALL_STAMP)
	$(POETRY) run pytest test --cov .

.PHONY: format
format: $(INSTALL_STAMP)
	$(POETRY) run isort --profile=black --lines-after-imports=2 .
	$(POETRY) run black .


.PHONY: lint
lint: $(INSTALL_STAMP)
	$(POETRY) run isort --profile=black --lines-after-imports=2 --check-only .
	$(POETRY) run black --check . --diff
	$(POETRY) run flake8 .
	$(POETRY) run mypy .
	$(POETRY) run bandit -x "./test/*" -r .

.PHONY: check
check: test lint

.PHONY: publish
publish:
	@test $${PATCH_VERSION?PATCH_VERSION expected}
	@test $${PYPI_USER?PYPI_USER expected}
	@test $${PYPI_PASSWORD?PYPI_PASSWORD expected}
	$(eval CURRENT_VERSION := $(shell $(POETRY) version --short))
	$(eval PARTIAL_VERSION=$(shell echo $(CURRENT_VERSION) | grep -Po '.*(?=\.)'))
	$(POETRY) version $(PARTIAL_VERSION).$(PATCH_VERSION)
	$(POETRY) publish --build --username $(PYPI_USER) --password $(PYPI_PASSWORD)
	$(POETRY) version $(CURRENT_VERSION)

.PHONY: clean
clean: ## Resets development environment.
	@echo 'cleaning repo...'
	@rm -rf `poetry env info -p`
	@rm -f .coverage
	@rm -rf .eggs/
	@rm -f .env
	@rm -rf .tox/
	@rm -rf build/
	@rm -rf dbt.egg-info/
	@rm -rf dist/
	@rm -rf logs/
	@rm -rf target/
	@rm .install.stamp
	@find . -type f -name '*.pyc' -delete
	@find . -depth -type d -name '__pycache__' -delete
	@echo 'done.'

.PHONY: help
help: ## Show this help message.
	@echo 'usage: make [target]'
	@echo
	@echo 'targets:'
	@grep -E '^[8+a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo
	
