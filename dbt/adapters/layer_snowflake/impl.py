from dbt.adapters.snowflake.impl import SnowflakeAdapter  # type:ignore

from common.adapter import LayerAdapter
from dbt.adapters.layer_snowflake.connections import LayerSnowflakeConnectionManager


class LayerSnowflakeAdapter(LayerAdapter, SnowflakeAdapter):
    ConnectionManager = LayerSnowflakeConnectionManager
    CASE_SENSITIVE = False
