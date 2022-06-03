import subprocess
import tempfile
from pathlib import Path
from typing import Iterable

import pystache  # type: ignore
import pytest


BIG_QUERY_KEY_FILE = Path(__file__).parent / ".big_query_key"
GITHUB_DBT_EXAMPLES_PROJECT = "layerai/examples-dbt"


class TestE2EExampleProjects:
    @pytest.fixture(scope="session")
    def dbt_examples_project_commit_sha(self) -> str:
        sha_file = Path(__file__).parent / "dbt_examples_project_commit_sha.txt"
        with open(str(sha_file), "r") as file:
            return file.read()

    @pytest.fixture(scope="session", autouse=True)
    def dbt_examples_project_dir(self, dbt_examples_project_commit_sha: str) -> Iterable[Path]:
        with tempfile.TemporaryDirectory() as tmp_path:
            project_dir = Path(tmp_path) / "examples_project"
            project_dir.mkdir()
            subprocess.run(
                ["git", "clone", f"https://github.com/{GITHUB_DBT_EXAMPLES_PROJECT}.git", str(project_dir)],
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["git", "-C", str(project_dir), "checkout", dbt_examples_project_commit_sha], stderr=subprocess.DEVNULL
            )
            yield project_dir

    @pytest.fixture(scope="session", autouse=True)
    def dbt_profiles_yaml(self) -> Iterable[Path]:
        with tempfile.TemporaryDirectory() as dbt_profiles_dir:
            dbt_profiles_template_path = Path(__file__).parent / "dbt_profiles_template.yaml"
            with open(str(dbt_profiles_template_path), "r") as file:
                dbt_profiles_template = file.read().strip("\n")
            context = {
                "dataset": "dbt_adapters_e2e_tests",
                "bq_key_file": str(BIG_QUERY_KEY_FILE),
                "bq_project": "layer-bigquery",
                "layer_config_file": str(Path("~/.layer/config.json").expanduser()),
                "layer_project": "Layer-dbt-adapter-e2e-tests",
            }
            rendered_profile = pystache.render(dbt_profiles_template, context)

            dbt_profiles_path = Path(dbt_profiles_dir) / "dbt_config" / "profiles.yml"
            dbt_profiles_path.parent.mkdir()
            with open(str(dbt_profiles_path), "w+") as file:
                file.write(rendered_profile)
            yield dbt_profiles_path

    @pytest.mark.parametrize(("project",), [("titanic",), ("sentiment_analysis",), ("cloth_detector",)])
    def test_run_example_project(self, project: str, dbt_examples_project_dir: Path, dbt_profiles_yaml: Path) -> None:
        project_path = dbt_examples_project_dir / project
        result = subprocess.run(
            ["dbt", "seed", "--project-dir", str(project_path), "--profiles-dir", str(dbt_profiles_yaml.parent)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        print(result.stdout)
        print(result.stderr)
        result = subprocess.run(
            ["dbt", "run", "--project-dir", str(project_path), "--profiles-dir", str(dbt_profiles_yaml.parent)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        print(result.stdout)
        print(result.stderr)
        assert "Completed successfully" in result.stdout
