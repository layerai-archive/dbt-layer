.DEFAULT_GOAL:=help

.PHONY: dev
dev: ## Installs development dependencies.
	@\
	pip install -r dev-requirements.txt 

.PHONY: install
install: ## Install the package locally.	
	@\
	pip install -e .

.PHONY: test
test: ## Runs unit tests.
	@\
	pytest test/unit

.PHONY: build
build: test ## Build the package

.PHONY: clean
clean: ## Resets development environment.
	@echo 'cleaning repo...'
	@rm -f .coverage
	@rm -rf .eggs/
	@rm -f .env
	@rm -rf .tox/
	@rm -rf build/
	@rm -rf dbt.egg-info/
	@rm -rf dist/
	@rm -rf logs/
	@rm -rf target/
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
	