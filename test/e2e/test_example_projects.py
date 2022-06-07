import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable

import pytest

from .conftest import REPOSITORY_ROOT_DIR


EXAMPLES_DIR = REPOSITORY_ROOT_DIR / "examples"


class TestE2EExampleProjects:
    @pytest.fixture(scope="session")
    def dbt_examples_dir(self) -> Iterable[Path]:
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_examples_dir = Path(tmp_path)
            shutil.copytree(EXAMPLES_DIR, tmp_examples_dir, dirs_exist_ok=True)
            yield tmp_examples_dir

    @pytest.mark.parametrize(
        ("example_project",),
        [
            ("titanic",),
            # ("sentiment_analysis",),
            # ("cloth_detector",),
        ],
    )
    def test_run_example_project(
        self, example_project: str, dbt_examples_dir: Path, dbt_profiles_yaml_bigquery: Path
    ) -> None:
        project_path = dbt_examples_dir / example_project
        result = subprocess.run(
            [
                "dbt",
                "seed",
                "--project-dir",
                str(project_path),
                "--profiles-dir",
                str(dbt_profiles_yaml_bigquery.parent),
            ],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        assert "Completed successfully" in result.stdout
        assert result.stderr == ""

        result = subprocess.run(
            [
                "dbt",
                "run",
                "--project-dir",
                str(project_path),
                "--profiles-dir",
                str(dbt_profiles_yaml_bigquery.parent),
            ],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        assert "Completed successfully" in result.stdout
        assert result.stderr == ""
