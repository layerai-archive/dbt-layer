INSTALL_STAMP := .install.stamp
POETRY := $(shell command -v poetry 2> /dev/null)
EXTRAS ?= "bigquery snowflake"
IN_VENV := $(shell echo $(CONDA_DEFAULT_ENV)$(CONDA_PREFIX)$(VIRTUAL_ENV))
REQUIRED_POETRY_VERSION := 1.2.0
UNAME_SYS := $(shell uname -s)
UNAME_ARCH := $(shell uname -m)
PROJECT_NAME := dbt-layer
CONDA_ENV_NAME := $(shell echo $(CONDA_DEFAULT_ENV))
E2E_TEST_SELECTOR := test/e2e

ifneq ($(shell $(POETRY) --version | sed -En 's/Poetry \(version (.*)\)/\1/p'), $(REQUIRED_POETRY_VERSION))
$(error "Please use Poetry version $(REQUIRED_POETRY_VERSION). Simply run: poetry self update $(REQUIRED_POETRY_VERSION)")
endif
