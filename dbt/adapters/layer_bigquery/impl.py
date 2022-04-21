from dbt.adapters.bigquery.impl import BigQueryAdapter
from dbt.adapters.bigquery.connections import BigQueryAdapterResponse
from dbt.adapters.layer_bigquery import LayerBigQueryConnectionManager
from dbt.clients import agate_helper
from dbt.events import AdapterLogger

import sqlparse


# layer specific code
logger = AdapterLogger("Layer")


class LayerAdapter(object):
    """
    Layer specific overrides
    """
    def load_dataframe(self, database, schema, table_name, agate_table,
                       column_override):
        logger.debug('Loading dataframe "{}.{}"', database, schema)
        return super().load_dataframe(database, schema, table_name, agate_table,
                       column_override)

    def execute(self, sql, **kwargs):
        layer_sql = parse_layer_sql(sql)
        if layer_sql is not None:
            response = BigQueryAdapterResponse(
                _message='Running Layer',
                rows_affected=0, # TODO
                code='LAYER',
                bytes_processed=0, # TODO
            )
            table = agate_helper.empty_table()
            return response, table
        # print(repr(sql))
        # print(self.config)
        # if sql represents a Layer build or train, call Layer, return the dataframe and call load_dataframe
        return super().execute(sql, **kwargs)


    # def _materialize_as_table(
    #     self, model, model_sql, decorator):
    #     """
    #     """
    #     logger.debug('Materializing as table "{}.{}"', model.get('database'), model.get('schema'))
    #     logger.debug('Materializing as table - sql "{}"', model_sql)
    #     return super()._materialize_as_table(model, model_sql, decorator)

def _clean_sql_tokens(tokens):
    """
    Removes whitespace and semicolon punctuation tokens
    """
    return [token for ix, token in enumerate(tokens)
            if not (
                    token.is_whitespace
                    or token.value == ';'
                    or token.value == '(' and ix == 0
                    or token.value == ')' and ix == len(tokens)-1
            )]


def parse_layer_sql(sql):
    """
    returns None if not a layer SQL statement
    returns a tuple of (source table, target table) if a layer SQL statement
    """
    parsed = sqlparse.parse(sql)
    if len(parsed) == 0:
        return

    # first strip out whitespace and punctuation from top level
    tokens1 = _clean_sql_tokens(parsed[0].tokens)

    # check the top level statement
    if not (len(tokens1) == 3
            and tokens1[0].ttype == sqlparse.tokens.DDL
            and tokens1[0].value == 'create or replace'
            and tokens1[1].ttype == sqlparse.tokens.Keyword
            and tokens1[1].value == 'table'
            and isinstance(tokens1[2], sqlparse.sql.Identifier)
            and tokens1[2].is_group
            ):
        return

    # then check the next level
    tokens2 = _clean_sql_tokens(tokens1[2].tokens)

    if not (len(tokens2) >= 2
            and isinstance(tokens2[-1], sqlparse.sql.Identifier)
            ):
        return


    target_name = ''.join(t.value for t in tokens2[:-1])

    # then check the next level
    tokens3 = _clean_sql_tokens(tokens2[-1].tokens)

    if not (len(tokens3) >= 2
            and isinstance(tokens3[-1], sqlparse.sql.Parenthesis)
            ):
        return

    # then check the next level
    tokens4 = _clean_sql_tokens(tokens3[-1].tokens)
    if not (len(tokens4) == 4
            and tokens4[0].ttype == sqlparse.tokens.DML
            and tokens4[0].value == 'select'
            and isinstance(tokens4[1], sqlparse.sql.Function)
            and isinstance(tokens4[3], sqlparse.sql.Identifier)
            ):
        return

    # then check the function
    function = tokens4[1].tokens
    if not (len(function) == 2
            and isinstance(function[0], sqlparse.sql.Identifier)
            and function[0].value in ('build', 'train')
            ):
        return

    return (function[0].value, target_name)

# end layer specific code

class LayerBigQueryAdapter(LayerAdapter, BigQueryAdapter):
    ConnectionManager = LayerBigQueryConnectionManager





def test1():
    sql = '\n\n  create or replace table `layer-dbt`.`titanic2`.`passenger_features`\n  \n  \n  OPTIONS()\n  as (\n    select build(*) from `layer-dbt`.`titanic2`.`passengers` as passengers\n  );\n  '
    print(parse_layer_sql(sql))


if __name__ == '__main__':
    test1()
