from dbt.adapters.base import BaseAdapter
from dbt.adapters.layer_bigquery import LayerBigQueryConnectionManager


class LayerBigQueryAdapter(BaseAdapter):
    ConnectionManager = LayerBigQueryConnectionManager
