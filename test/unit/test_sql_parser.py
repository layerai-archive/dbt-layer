from common.sql_parser import LayerSQL, LayerSQLParser


def test_sql_parser() -> None:
    sql = """
  create or replace table `layer-bigquery`.`titanic`.`passenger_features`
  OPTIONS()
  as (
    select layer.build(*) from `layer-bigquery`.`titanic`.`passengers` as passengers
  );
"""
    parsed = LayerSQLParser.parse(sql=sql)
    assert parsed
    assert isinstance(parsed, LayerSQL)
    assert parsed.function_type == "build"
    assert parsed.source_name == "`layer-bigquery`.`titanic`.`passengers`"
    assert parsed.target_name == "`layer-bigquery`.`titanic`.`passenger_features`"
