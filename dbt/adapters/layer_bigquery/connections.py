from dataclasses import dataclass

from dbt.adapters.bigquery.connections import (  # type:ignore
    BigQueryConnectionManager,
    BigQueryCredentials,
)

from common.credentials import LayerCredentials


@dataclass
class LayerBigQueryCredentials(LayerCredentials, BigQueryCredentials):
    @property
    def type(self) -> str:
        return "layer_bigquery"


class LayerBigQueryConnectionManager(BigQueryConnectionManager):
    TYPE = "layer_bigquery"
