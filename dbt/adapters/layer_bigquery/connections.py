from dataclasses import dataclass
from typing import Any, Dict, Optional

from dbt.adapters.bigquery.connections import (  # type:ignore
    BigQueryConnectionManager,
    BigQueryCredentials,
)


@dataclass
class LayerBigQueryCredentials(BigQueryCredentials):
    # Layer config json creds
    layer_configfile: Optional[str] = None
    layer_configfile_json: Optional[Dict[str, Any]] = None
    layer_project: Optional[str] = None

    @property
    def type(self) -> str:
        return "layer_bigquery"


class LayerBigQueryConnectionManager(BigQueryConnectionManager):
    TYPE = "layer_bigquery"
