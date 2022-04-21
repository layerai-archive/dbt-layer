from dataclasses import dataclass
from typing import Optional, Any, Dict

from dbt.adapters.bigquery.connections import BigQueryCredentials, BigQueryConnectionManager

# layer specific code

class LayerConnectionManager(object):
    """
    Layer specific overrides
    """

    # def execute(self, sql, **kwargs):
    #     print(repr(sql))
    #     # conn = self.get_thread_connection()
    #     return super(self).execute(sql, **kwargs)


# end layer specific code


@dataclass
class LayerBigQueryCredentials(BigQueryCredentials):
    # Layer config json creds
    layer_configfile: Optional[str] = None
    layer_configfile_json: Optional[Dict[str, Any]] = None

    @property
    def type(self):
        return 'layer_bigquery'


class LayerBigQueryConnectionManager(LayerConnectionManager, BigQueryConnectionManager):
    TYPE = 'layer_bigquery'
