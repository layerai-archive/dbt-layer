import pathlib
import re

import toml


def test_dbt_core_version() -> None:
    repo_root = pathlib.Path(__file__).parent.parent.parent

    dbt_version_file = repo_root / "dbt" / "adapters" / "layer_bigquery" / "__version__.py"
    with open(dbt_version_file) as f:
        content = f.read()
        match = re.search('version = "(.*)"', content)
        if match:
            dbt_version = match.group(1)
        else:
            raise Exception("Failed to get version")

    pyproject_file = repo_root / "pyproject.toml"

    with open(pyproject_file) as f:
        pyproject = toml.load(f)
        dbt_core_version = pyproject["tool"]["poetry"]["dependencies"]["dbt-core"]

    assert dbt_core_version == dbt_version
