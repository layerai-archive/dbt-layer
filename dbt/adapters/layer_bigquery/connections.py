from dataclasses import dataclass
from typing import Optional, Any, Dict

from dbt.adapters.bigquery.connections import BigQueryCredentials, BigQueryConnectionManager


@dataclass
class LayerBigQueryCredentials(BigQueryCredentials):
    # Layer config json creds
    layer_configfile: Optional[str] = None
    layer_configfile_json: Optional[Dict[str, Any]] = None
    layer_project: Optional[str] = None

    @property
    def type(self):
        return 'layer_bigquery'


class LayerBigQueryConnectionManager(BigQueryConnectionManager):
    TYPE = 'layer_bigquery'
