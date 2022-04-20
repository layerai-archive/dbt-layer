from dbt.adapters.base import BaseAdapter
from dbt.adapters.dbt-layer-bigquery import LayerBigQueryConnectionManager


class LayerBigQueryAdapter(BaseAdapter):
    ConnectionManager = LayerBigQueryConnectionManager
