from dbt.adapters.base import AdapterPlugin

from dbt.adapters.layer_bigquery.connections import (
    LayerBigQueryConnectionManager,
    LayerBigQueryCredentials,
)
from dbt.adapters.layer_bigquery.impl import LayerBigQueryAdapter
from dbt.include import layer_bigquery


Plugin = AdapterPlugin(
    adapter=LayerBigQueryAdapter,
    credentials=LayerBigQueryCredentials,
    include_path=layer_bigquery.PACKAGE_PATH,
)
