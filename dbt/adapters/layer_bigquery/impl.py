from dbt.adapters.bigquery.impl import BigQueryAdapter  # type:ignore
from layer_dbt.dbt.adapter import LayerAdapter

from .connections import LayerBigQueryConnectionManager


class LayerBigQueryAdapter(LayerAdapter, BigQueryAdapter):
    ConnectionManager = LayerBigQueryConnectionManager
