from dbt.adapters.dbt-layer-bigquery.connections import LayerBigQueryConnectionManager
from dbt.adapters.dbt-layer-bigquery.connections import LayerBigQueryCredentials
from dbt.adapters.dbt-layer-bigquery.impl import LayerBigQueryAdapter

from dbt.adapters.base import AdapterPlugin
from dbt.include import dbt-layer-bigquery


Plugin = AdapterPlugin(
    adapter=LayerBigQueryAdapter,
    credentials=LayerBigQueryCredentials,
    include_path=dbt-layer-bigquery.PACKAGE_PATH)
