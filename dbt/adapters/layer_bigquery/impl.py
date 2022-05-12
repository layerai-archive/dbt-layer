from common.adapter import LayerAdapter
from dbt.adapters.bigquery.impl import BigQueryAdapter  # type:ignore

from .connections import LayerBigQueryConnectionManager


class LayerBigQueryAdapter(LayerAdapter, BigQueryAdapter):
    ConnectionManager = LayerBigQueryConnectionManager
