from dataclasses import dataclass

from dbt.adapters.bigquery.connections import BigQueryCredentials, BigQueryConnectionManager


@dataclass
class LayerBigQueryCredentials(BigQueryCredentials):
    @property
    def type(self):
        return 'layer_bigquery'


class LayerBigQueryConnectionManager(BigQueryConnectionManager):
    TYPE = 'layer_bigquery'
