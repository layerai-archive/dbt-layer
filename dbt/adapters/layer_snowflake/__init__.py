from dbt.adapters.base import AdapterPlugin  # type: ignore

from dbt.adapters.layer_snowflake.connections import LayerSnowflakeCredentials
from dbt.adapters.layer_snowflake.impl import LayerSnowflakeAdapter
from dbt.include import layer_snowflake


Plugin = AdapterPlugin(
    adapter=LayerSnowflakeAdapter,
    credentials=LayerSnowflakeCredentials,
    include_path=layer_snowflake.PACKAGE_PATH,
    dependencies=["snowflake"],
)
