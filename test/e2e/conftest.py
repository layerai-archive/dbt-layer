import json
import logging
import os
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

BIGQUERY_PROJECT_NAME = "layer-bigquery"
BIGQUERY_CREDENTIALS = os.getenv("BIGQUERY_CREDENTIALS") or "{}"

SNOWFLAKE_PROJECT_NAME = "layer-snowflake"
SNOWFLAKE_CREDENTIALS = os.getenv("SNOWFLAKE_CREDENTIALS") or "{}"


@pytest.fixture()
def test_project_name(request: pytest.FixtureRequest, adapter_type: str) -> str:
    test_name_parametrized: str
    if request.cls is not None:
        test_name_parametrized = f"{request.cls.__module__}_{request.cls.__name__}"
    else:
        test_name_parametrized = f"{request.module.__name__}"
    test_name_parametrized = f"{test_name_parametrized}_{request.node.name}"
    test_name_parametrized = test_name_parametrized.replace("[", "_").replace("]", "")
    # cut off prefixing modules
    test_name_parametrized = test_name_parametrized.split(".")[-1]

    return f"dbt_adapters_e2e_{adapter_type}_{test_name_parametrized}_{str(uuid.uuid4())[:8]}"


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
def dbt_profiles_yaml(adapter_type: str, test_project_name: str) -> Iterable[Path]:
    if adapter_type == "bigquery":
        yield from dbt_profiles_yaml_bigquery(test_project_name)
    elif adapter_type == "snowflake":
        yield from dbt_profiles_yaml_snowflake(test_project_name)
    else:
        raise Exception(f"Invalid adapter type: {adapter_type!r}")


def dbt_profiles_yaml_bigquery(test_project_name: str) -> Iterable[Path]:
    with tempfile.TemporaryDirectory() as dbt_profiles_dir:
        bigquery_credentials_file = Path(dbt_profiles_dir) / "bigquery_credentials.json"
        with open(bigquery_credentials_file, "w") as f:
            f.write(BIGQUERY_CREDENTIALS)

        dbt_profiles_path = Path(dbt_profiles_dir) / "dbt_config" / "profiles.yml"
        dbt_profiles_path.parent.mkdir()

        dbt_profiles = f"""
layer-profile:
  outputs:
    dev:
      dataset: {test_project_name}
      timeout_seconds: 300
      keyfile: {bigquery_credentials_file}
      location: US
      method: service-account
      priority: interactive
      project: {BIGQUERY_PROJECT_NAME}
      threads: 1
      type: layer_bigquery
      fixed_retries: 1
  target: dev
        """
        with open(dbt_profiles_path, "w") as file:
            file.write(dbt_profiles)

        yield dbt_profiles_path

        clean_up_bigquery_dataset(test_project_name)


def clean_up_bigquery_dataset(test_project_name: str) -> None:
    # clean up the bigquery dataset after tests are run
    from google.cloud import bigquery  # type: ignore
    from google.oauth2 import service_account  # type: ignore

    with tempfile.TemporaryDirectory() as tmp_dir:
        bigquery_credentials_file = Path(tmp_dir) / "bigquery_credentials.json"
        with open(bigquery_credentials_file, "w") as f:
            f.write(BIGQUERY_CREDENTIALS)
        credentials = service_account.Credentials.from_service_account_file(
            bigquery_credentials_file,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

    client = bigquery.Client(
        credentials=credentials,
        project=credentials.project_id,
    )

    dataset_id = f"{BIGQUERY_PROJECT_NAME}.{test_project_name}"
    client.delete_dataset(dataset_id, delete_contents=True, not_found_ok=True)


def dbt_profiles_yaml_snowflake(test_project_name: str) -> Iterable[Path]:
    credentials = json.loads(SNOWFLAKE_CREDENTIALS)
    with tempfile.TemporaryDirectory() as dbt_profiles_dir:

        dbt_profiles_path = Path(dbt_profiles_dir) / "dbt_config" / "profiles.yml"
        dbt_profiles_path.parent.mkdir()

        dbt_profiles = f"""
layer-profile:
  outputs:
    dev:
      type: layer_snowflake
      account: {credentials['account']}

      user: {credentials['user']}
      password: {credentials['password']}
      role: {credentials['role']}

      database: {credentials['database']}
      warehouse: {credentials['warehouse']}
      schema: {test_project_name}

  target: dev
        """
        with open(dbt_profiles_path, "w") as file:
            file.write(dbt_profiles)

        yield dbt_profiles_path

        clean_up_snowflake_schema(test_project_name)


def clean_up_snowflake_schema(test_project_name: str) -> None:
    credentials = json.loads(SNOWFLAKE_CREDENTIALS)
    import snowflake.connector

    with snowflake.connector.connect(
        user=credentials["user"],
        password=credentials["password"],
        role=credentials["role"],
        account=credentials["account"],
        warehouse=credentials["warehouse"],
        database=credentials["database"],
        schema=test_project_name,
    ) as conn:
        # escape the identifier
        schema_name = (
            f"{escape_snowflake_identifier(credentials['database'])}.{escape_snowflake_identifier(test_project_name)}"
        )
        conn.cursor().execute(f"DROP SCHEMA {schema_name}")


def escape_snowflake_identifier(identifier: str) -> str:
    return f'''"{identifier.replace('"', '""').upper()}"'''
