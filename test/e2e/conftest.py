import logging
import tempfile
import uuid
from pathlib import Path
from typing import Iterable, Iterator

import pytest

from layer.clients.layer import LayerClient
from layer.config import ClientConfig, Config, ConfigManager


logger = logging.getLogger(__name__)

E2E_TEST_DIR = Path(__file__).parent
REPOSITORY_ROOT_DIR = E2E_TEST_DIR.parent.parent
BIGQUERY_KEY_FILE = E2E_TEST_DIR / ".big_query_key"
BIGQUERY_PROFILES_TEMPLATE_FILE = E2E_TEST_DIR / "profiles_template_bigquery.yaml"
BIGQUERY_PROJECT_NAME = "layer-bigquery"


@pytest.fixture()
def test_project_name(request: pytest.FixtureRequest) -> str:
    test_name_parametrized: str
    if request.cls is not None:
        test_name_parametrized = f"{request.cls.__module__}_{request.cls.__name__}"
    else:
        test_name_parametrized = f"{request.module.__name__}"
    test_name_parametrized = f"{test_name_parametrized}_{request.node.name}"
    test_name_parametrized = test_name_parametrized.replace("[", "_").replace("]", "")
    # cut off prefixing modules
    test_name_parametrized = test_name_parametrized.split(".")[-1]

    return f"dbt_adapters_e2e_{test_name_parametrized}_{str(uuid.uuid4())[:8]}"


@pytest.fixture()
async def layer_config() -> Config:
    return await ConfigManager().refresh(allow_guest=True)


@pytest.fixture()
async def layer_client_config(layer_config: Config) -> ClientConfig:
    return layer_config.client


@pytest.fixture()
def layer_client(layer_client_config: ClientConfig) -> Iterator[LayerClient]:
    with LayerClient(layer_client_config, logger).init() as client:
        yield client


@pytest.fixture()
def bigquery_dataset(test_project_name: str) -> Iterator[str]:
    yield test_project_name

    # clean up the bigquery dataset after tests are run
    from google.cloud import bigquery  # type: ignore
    from google.oauth2 import service_account  # type: ignore

    credentials = service_account.Credentials.from_service_account_file(
        BIGQUERY_KEY_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    client = bigquery.Client(
        credentials=credentials,
        project=credentials.project_id,
    )

    dataset_id = f"{BIGQUERY_PROJECT_NAME}.{test_project_name}"
    client.delete_dataset(dataset_id, delete_contents=True, not_found_ok=True)


@pytest.fixture()
def dbt_profiles_yaml_bigquery(bigquery_dataset: str) -> Iterable[Path]:
    with tempfile.TemporaryDirectory() as dbt_profiles_dir:
        dbt_profiles_path = Path(dbt_profiles_dir) / "dbt_config" / "profiles.yml"
        dbt_profiles_path.parent.mkdir()

        dbt_profiles = """
layer-profile:
  outputs:
    dev:
      dataset: {bq_dataset}
      timeout_seconds: 300
      keyfile: {bq_key_file}
      location: US
      method: service-account
      priority: interactive
      project: {bq_project}
      threads: 1
      type: layer_bigquery
      fixed_retries: 1
  target: dev
        """.format(
            bq_dataset=bigquery_dataset,
            bq_key_file=str(BIGQUERY_KEY_FILE),
            bq_project=BIGQUERY_PROJECT_NAME,
        )
        with open(dbt_profiles_path, "w+") as file:
            file.write(dbt_profiles)

        yield dbt_profiles_path
