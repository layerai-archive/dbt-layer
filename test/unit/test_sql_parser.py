from common.sql_parser import LayerPredictFunction, LayerSqlFunction, LayerSQLParser


def test_sql_parser_with_build() -> None:
    sql = """
  create or replace table `layer-bigquery`.`titanic`.`passenger_features`
  OPTIONS()
  as (
    select layer.build(*) from `layer-bigquery`.`titanic`.`passengers` as passengers
  );
"""
    parsed = LayerSQLParser().parse(sql=sql)
    assert parsed
    assert isinstance(parsed, LayerSqlFunction)
    assert parsed.function_type == "build"
    assert parsed.source_name == "`layer-bigquery`.`titanic`.`passengers`"
    assert parsed.target_name == "`layer-bigquery`.`titanic`.`passenger_features`"


def test_sql_parser_with_predict() -> None:
    sql = """
  create or replace table `layer-bigquery`.`ecommerce`.`customer_features`
  OPTIONS()
  as (
    SELECT customer_id, product_id, customer_age,
    layer.predict("layer/ecommerce/models/buy_it_again:latest", ARRAY[customer_id, product_id]) as likely_to_buy_score
    FROM `layer-bigquery`.`ecommerce`.`customers`
  );
"""
    parsed = LayerSQLParser().parse(sql=sql)
    assert parsed
    assert isinstance(parsed, LayerPredictFunction)
    assert parsed.function_type == "predict"
    assert parsed.source_name == "`layer-bigquery`.`ecommerce`.`customers`"
    assert parsed.target_name == "`layer-bigquery`.`ecommerce`.`customer_features`"
    assert parsed.model_name == "layer/ecommerce/models/buy_it_again:latest"
    assert parsed.select_columns == ["customer_id", "product_id", "customer_age"]
    assert parsed.predict_columns == ["customer_id", "product_id"]
    assert parsed.sql == "select customer_id, product_id, customer_age from `layer-bigquery`.`ecommerce`.`customers`"


def test_sql_parser_with_predict_argument_column_does_not_exist_select_columns() -> None:
    sql = """
  create or replace table `layer-bigquery`.`ecommerce`.`customer_features`
  OPTIONS()
  as (
    SELECT customer_id, product_id, customer_age,
    layer.predict("layer/ecommerce/models/buy_it_again:latest", ARRAY[customer_id, product_id, customer_region])
    FROM `layer-bigquery`.`ecommerce`.`customers`
    where customer_age > 40 order by customer_id asc limit 1
  );
"""
    parsed = LayerSQLParser().parse(sql=sql)
    assert parsed
    assert isinstance(parsed, LayerPredictFunction)
    assert parsed.function_type == "predict"
    assert parsed.source_name == "`layer-bigquery`.`ecommerce`.`customers`"
    assert parsed.target_name == "`layer-bigquery`.`ecommerce`.`customer_features`"
    assert parsed.model_name == "layer/ecommerce/models/buy_it_again:latest"
    assert parsed.select_columns == ["customer_id", "product_id", "customer_age"]
    assert parsed.predict_columns == ["customer_id", "product_id", "customer_region"]
    assert (
        parsed.sql
        == "select customer_id, product_id, customer_age from `layer-bigquery`.`ecommerce`.`customers`"
        + " where customer_age > 40 order by customer_id asc limit 1"
    )
