#
# Environment Management Makefile

define conda_environment_file
name: sdk\\n
channels:\\n
  - default\\n
  - apple\\n
  - conda-forge\\n
dependencies:\\n
  - python=$(shell cat .python-version)\\n
  - pip\\n
  - poetry=$(REQUIRED_POETRY_VERSION)
endef

.PHONY: create-environment 
create-environment: create-environment-$(UNAME_SYS) ## Set up virtual environment

.PHONY: create-environment-Linux
create-environment-Linux: .python-version
ifeq ($(shell which pyenv),)
	@echo "pyenv is not Installed, please install before creating an environment"
	@exit 1
else
	@pyenv install -s $(shell cat $<)
	@echo "pyenv Python version $(shell cat $<) installed."
	@echo "Activate shell with poetry shell"
endif

.PHONY: create-environment-Darwin
create-environment-Darwin:
ifeq ($(UNAME_ARCH), arm64)
ifdef CONDA_ENV_NAME
	$(shell echo $(conda_environment_file) > .environment.M1.yml)
	$(CONDA_EXE) env update -p build/$(PROJECT_NAME) -f .environment.M1.yml
	@echo
	@echo "Conda env is available and can be activated."
else
	$(error Unsupported Environment. Please use conda)
endif
endif

.PHONY: delete-environment
delete-environment: delete-environment-$(UNAME_SYS)  ## Delete the virtual environment

.PHONY: delete-environment-Linux
delete-environment-Linux:
	@echo "No action needed"

.PHONY: delete-environment-Darwin
delete-environment-Darwin:
ifeq ($(UNAME_ARCH), arm64)
	@echo "Deleting conda environment."
	rm -fr build/$(PROJECT_NAME)
endif

clean: delete-environment
