from dbt.adapters.bigquery.impl import BigQueryAdapter

from dbt.adapters.layer_bigquery import LayerBigQueryConnectionManager
from layer_dbt.dbt.adapter import LayerAdapter


class LayerBigQueryAdapter(LayerAdapter, BigQueryAdapter):
    ConnectionManager = LayerBigQueryConnectionManager
