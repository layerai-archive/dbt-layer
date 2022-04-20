from dbt.adapters.bigquery.impl import BigQueryAdapter
from dbt.adapters.layer_bigquery import LayerBigQueryConnectionManager


class LayerBigQueryAdapter(BigQueryAdapter):
    ConnectionManager = LayerBigQueryConnectionManager
