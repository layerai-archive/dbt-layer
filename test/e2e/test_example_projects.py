import shutil
import tempfile
from pathlib import Path
from typing import Iterable, List

import pytest
from dbt.contracts.results import RunExecutionResult
from dbt.logger import log_manager
from dbt.main import handle_and_check

from .conftest import REPOSITORY_ROOT_DIR


EXAMPLES_DIR = REPOSITORY_ROOT_DIR / "examples"


class TestE2EExampleProjects:
    @pytest.fixture(scope="session")
    def dbt_examples_dir(self) -> Iterable[Path]:
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_examples_dir = Path(tmp_path)
            shutil.copytree(EXAMPLES_DIR, tmp_examples_dir, dirs_exist_ok=True)
            yield tmp_examples_dir

    def test_run_titanic(self, dbt_examples_dir: Path, dbt_profiles_yaml_bigquery: Path) -> None:
        project_path = dbt_examples_dir / "titanic"

        results = run_dbt(
            ["seed", "--project-dir", str(project_path), "--profiles-dir", str(dbt_profiles_yaml_bigquery.parent)]
        )
        assert len(results.results) == 1
        resp0 = results.results[0].adapter_response
        assert resp0["rows_affected"] == 891
        assert resp0["code"] == "INSERT"

        results = run_dbt(
            ["run", "--project-dir", str(project_path), "--profiles-dir", str(dbt_profiles_yaml_bigquery.parent)]
        )
        assert len(results.results) == 2
        resp0 = results.results[0].adapter_response
        assert resp0["code"] == "CREATE TABLE"
        assert resp0["rows_affected"] == 891
        resp1 = results.results[1].adapter_response
        assert resp1["code"] == "LAYER PREDICT"
        assert resp1["rows_affected"] == 891

    def test_run_sentiment_analysis(self, dbt_examples_dir: Path, dbt_profiles_yaml_bigquery: Path) -> None:
        project_path = dbt_examples_dir / "sentiment_analysis"

        results = run_dbt(
            ["seed", "--project-dir", str(project_path), "--profiles-dir", str(dbt_profiles_yaml_bigquery.parent)]
        )
        assert len(results.results) == 1
        resp0 = results.results[0].adapter_response
        assert resp0["rows_affected"] == 20
        assert resp0["code"] == "INSERT"

        results = run_dbt(
            ["run", "--project-dir", str(project_path), "--profiles-dir", str(dbt_profiles_yaml_bigquery.parent)]
        )
        assert len(results.results) == 1
        resp0 = results.results[0].adapter_response
        assert resp0["code"] == "LAYER PREDICT"
        assert resp0["rows_affected"] == 20


def run_dbt(args: List[str], expect_success: bool = True) -> RunExecutionResult:
    log_manager.reset_handlers()
    results, succeeded = handle_and_check(args=args)
    assert succeeded == expect_success
    return results
