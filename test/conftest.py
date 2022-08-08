import logging

import pytest


logger = logging.getLogger(__name__)

ALL_ADAPTERS = ["bigquery", "snowflake"]


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    adapter_type = metafunc.config.option.adapter
    if "adapter_type" in metafunc.fixturenames:
        metafunc.parametrize("adapter_type", ALL_ADAPTERS if adapter_type is None else [adapter_type], indirect=True)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--adapter", action="store", choices=ALL_ADAPTERS)


@pytest.fixture(scope="session")
def adapter_type(request: pytest.FixtureRequest) -> str:
    """
    This fixture is parametrized by pytest_generate_tests
    By default it iterates over all adapter types, but if the --adapter
    option is given, it only iterates over that adapter type
    """
    logger.info("running e2e tests for adapter type %s", adapter_type)
    return request.param  # type: ignore
