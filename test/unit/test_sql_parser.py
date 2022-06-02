import pytest

from common.sql_parser import (
    LayerAutoMLFunction,
    LayerPredictFunction,
    LayerSQLParser,
    LayerTrainFunction,
)


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


def test_sql_parser_for_train() -> None:
    sql = """
  create or replace table `layer-bigquery`.`ecommerce`.`customer_features`
  OPTIONS()
  as (
    SELECT
    layer.train(ARRAY[customer_id, product_id, customer_age])
    FROM `layer-bigquery`.`ecommerce`.`customers`
  );
"""
    parsed = LayerSQLParser().parse(sql=sql)
    assert parsed
    assert isinstance(parsed, LayerTrainFunction)
    assert parsed.function_type == "train"
    assert parsed.source_name == "`layer-bigquery`.`ecommerce`.`customers`"
    assert parsed.target_name == "`layer-bigquery`.`ecommerce`.`customer_features`"
    assert parsed.train_columns == ["customer_id", "product_id", "customer_age"]


def test_parser_for_pass_through() -> None:
    sql = """
        create or replace table `layer-bigquery`.`ecommerce`.`passenger_features`
        OPTIONS()
        as (
        SELECT
        case when sex = 'female' then 0 end as sex
        FROM `layer-bigquery`.`ecommerce`.`customers`
        );
    """
    parsed = LayerSQLParser().parse(sql=sql)
    assert not parsed


def test_sql_parser_for_train_with_asterisk() -> None:
    sql = """
  create or replace table `layer-bigquery`.`ecommerce`.`customer_features`
  OPTIONS()
  as (
    SELECT
    layer.train(*)
    FROM `layer-bigquery`.`ecommerce`.`customers`
  );
"""
    parsed = LayerSQLParser().parse(sql=sql)
    assert parsed
    assert isinstance(parsed, LayerTrainFunction)
    assert parsed.function_type == "train"
    assert parsed.source_name == "`layer-bigquery`.`ecommerce`.`customers`"
    assert parsed.target_name == "`layer-bigquery`.`ecommerce`.`customer_features`"
    assert parsed.train_columns == ["*"]


def test_sql_parser_for_train_with_no_column_specified() -> None:
    sql = """
  create or replace table `layer-bigquery`.`ecommerce`.`customer_features`
  OPTIONS()
  as (
    SELECT
    layer.train()
    FROM `layer-bigquery`.`ecommerce`.`customers`
  );
"""
    parsed = LayerSQLParser().parse(sql=sql)
    assert parsed
    assert isinstance(parsed, LayerTrainFunction)
    assert parsed.function_type == "train"
    assert parsed.source_name == "`layer-bigquery`.`ecommerce`.`customers`"
    assert parsed.target_name == "`layer-bigquery`.`ecommerce`.`customer_features`"
    assert parsed.train_columns == ["*"]


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
        == "select customer_id, product_id, customer_age, customer_region from `layer-bigquery`.`ecommerce`.`customers`"
        + " where customer_age > 40 order by customer_id asc limit 1"
    )


def test_sql_parser_with_predict_argument_single_column() -> None:
    sql = """
  create or replace table `layer-bigquery`.`ecommerce`.`customer_features`
  OPTIONS()
  as (
    SELECT customer_id, product_id, customer_age,
    layer.predict("layer/ecommerce/models/buy_it_again:latest", ARRAY[customer_region])
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
    assert parsed.predict_columns == ["customer_region"]
    assert (
        parsed.sql
        == "select customer_id, product_id, customer_age, customer_region from `layer-bigquery`.`ecommerce`.`customers`"
        + " where customer_age > 40 order by customer_id asc limit 1"
    )


def test_sql_parser_with_predict_missing_array() -> None:
    sql = """
  create or replace table `layer-bigquery`.`ecommerce`.`customer_features`
  OPTIONS()
  as (
    SELECT customer_id, product_id, customer_age,
    layer.predict("layer/ecommerce/models/buy_it_again:latest") as likely_to_buy_score
    FROM `layer-bigquery`.`ecommerce`.`customers`
  );
"""
    with pytest.raises(ValueError, match=r".*Invalid predict function syntax.*"):
        LayerSQLParser().parse(sql=sql)


def test_sql_parser_with_predict_missing_model_name() -> None:
    sql = """
  create or replace table `layer-bigquery`.`ecommerce`.`customer_features`
  OPTIONS()
  as (
    SELECT customer_id, product_id, customer_age,
    layer.predict() as likely_to_buy_score
    FROM `layer-bigquery`.`ecommerce`.`customers`
  );
"""
    with pytest.raises(ValueError, match=r".*Invalid predict function syntax.*"):
        LayerSQLParser().parse(sql=sql)


def test_sql_parser_with_unknown_layer_function() -> None:
    sql = """
  create or replace table `layer-bigquery`.`ecommerce`.`customer_features`
  OPTIONS()
  as (
    SELECT customer_id, product_id, customer_age,
    layer.non_existing(ARRAY[customer_id, product_id, customer_region])
    FROM `layer-bigquery`.`ecommerce`.`customers`
  );
"""
    with pytest.raises(ValueError, match=r".*Unsupported function: non_existing.*"):
        LayerSQLParser().parse(sql=sql)


def test_sql_parser_with_typo_in_layer_prefix() -> None:
    sql = """
  create or replace table `layer-bigquery`.`ecommerce`.`customer_features`
  OPTIONS()
  as (
    SELECT customer_id, product_id, customer_age,
    llayer.non_existing(ARRAY[customer_id, product_id, customer_region])
    FROM `layer-bigquery`.`ecommerce`.`customers`
  );
"""
    parsed = LayerSQLParser().parse(sql=sql)
    assert not parsed


def test_sql_parser_with_automl_function() -> None:
    sql = """
  create or replace table `layer-bigquery`.`titanic`.`Survived`
  OPTIONS()
  as (
    SELECT layer.automl("classifier", ARRAY[Age, Sex, Pclass, SibSp, Parch, Fare], Survived)
    FROM `layer-bigquery`.`titanic`.`passenger_features`
  );
"""
    parsed = LayerSQLParser().parse(sql=sql)
    assert parsed
    assert isinstance(parsed, LayerAutoMLFunction)
    assert parsed.function_type == "automl"
    assert parsed.source_name == "`layer-bigquery`.`titanic`.`passenger_features`"
    assert parsed.target_name == "`layer-bigquery`.`titanic`.`Survived`"
    assert parsed.feature_columns == ["Age", "Sex", "Pclass", "SibSp", "Parch", "Fare"]
    assert parsed.target_column == "Survived"
    assert parsed.model_type == "classifier"
    assert (
        parsed.sql
        == "select Age, Sex, Pclass, SibSp, Parch, Fare, Survived from `layer-bigquery`.`titanic`.`passenger_features`"
    )
