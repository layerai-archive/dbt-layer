from dataclasses import dataclass

from dbt.adapters.snowflake.connections import (  # type:ignore
    SnowflakeConnectionManager,
    SnowflakeCredentials,
)

from common.credentials import LayerCredentials


@dataclass
class LayerSnowflakeCredentials(LayerCredentials, SnowflakeCredentials):
    @property
    def type(self) -> str:
        return "layer_snowflake"


class LayerSnowflakeConnectionManager(SnowflakeConnectionManager):
    TYPE = "layer_snowflake"
