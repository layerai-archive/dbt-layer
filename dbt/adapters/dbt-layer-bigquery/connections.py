from dataclasses import dataclass

from dbt.adapters.base import Credentials
from dbt.adapters.base import BaseConnectionManager


@dataclass
class LayerBigQueryCredentials(Credentials):
    # Add credentials members here, like:
    # host: str
    # port: int
    # username: str
    # password: str

    @property
    def type(self):
        return 'dbt-layer-bigquery'

    def _connection_keys(self):
        # return an iterator of keys to pretty-print in 'dbt debug'.
        # Omit fields like 'password'!
        raise NotImplementedError


class LayerBigQueryConnectionManager(BaseConnectionManager):
    TYPE = 'dbt-layer-bigquery'
