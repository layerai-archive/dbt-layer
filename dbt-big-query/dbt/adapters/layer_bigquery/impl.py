from dbt.adapters.bigquery.impl import BigQueryAdapter  # type:ignore

from common.adapter import LayerAdapter
from dbt.adapters.layer_bigquery.connections import LayerBigQueryConnectionManager


class LayerBigQueryAdapter(LayerAdapter, BigQueryAdapter):
    ConnectionManager = LayerBigQueryConnectionManager
