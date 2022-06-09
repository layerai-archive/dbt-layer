<p align="center">
    <br>
    <a href="https://layer.ai">
          <img src="https://app.layer.ai/assets/layer_wordmark_black.png" width="40%"
alt="Layer"/>
    </a>
    <br>
</p>

<p align="center">
    <a href="https://github.com/layerai/dbt-adapters/blob/main/LICENSE">
        <img alt="License" src="https://img.shields.io/github/license/layerai/dbt-adapters.svg?color=yellow">
    </a>
    <a href="https://pypi.python.org/pypi/dbt-layer-big
query">
        <img alt="PyPI" src="https://img.shields.io/pypi/v/layer.svg">
    </a>
    <a href="https://github.com/layerai/.github/blob/main/CODE_OF_CONDUCT.md">
        <img alt="Contributor Covenant" src="https://img.shields.io/badge/contributor%20covenant-v2.1%20adopted-blueviolet.svg">
    </a>
</p>

# Layer dbt Adapter for BigQuery (Beta)

This adapter runs ML pipelines inside dbt dag with BigQuery as the backing data warehouse. With Layer dbt Adapter you can:

- Score your data with a machine learning model from Layer.
- Train an AutoML model with your data.
- Train a custom machine learning model with your data _[coming soon...]_

To learn more about Layer:

https://layer.ai

## Getting started
To immediately start  using Layer inside your dbt DAG, install the Layer dbt Adapter for BigQuery:
```shell
pip install dbt-layer-bigquery -U
```

Add the Layer dbt Adapter to your BigQuery profile. An example profile:
```yaml
layer-profile:
  target: dev
  outputs:
    dev:
      type: layer_bigquery
      method: service-account
      project: [GCP project id]
      dataset: [the name of your dbt dataset]
      threads: [1 or more]
      keyfile: [/path/to/bigquery/keyfile.json]
      layer_api_key: [the API Key to access your Layer account (opt)]
```

Now, start making predictions directly in your dbt DAG:

```sql
select id,
       review,
       layer.predict("layer/nlptown/models/sentimentanalysis", ARRAY[review])
from {{ref('reviews')}}
```

## Examples
Check out the examples we have prepared for you:

- [Predicting survials of Titanic](https://github.com/layerai/examples-dbt/tree/main/titanic) - Predicts the survivals of the Titanic disaster.
- [Sentiment analysis of product reviews](https://github.com/layerai/examples-dbt/tree/main/sentiment_analysis) - An example that shows how to make multi-language sentiment analysis.
- [Object detection in product images](https://github.com/layerai/examples-dbt/tree/main/cloth_detector) - Detects cloths from product images using a pretrained computer vision model.
- [Review Scores Prediction with AutoML](https://github.com/layerai/dbt-layer/tree/main/examples/order_review_predictionr) - Train an AutoML model to predict the review scores.

## Quick Tour

### Prediction

You can use any Layer ML model to make predictions with your dbt models.

_Syntax:_
```
layer.predict("LAYER_MODEL_PATH", ARRAY[FEATURES])
```

_Parameters:_

| Syntax    | Description |
| --------- | ----------- |
| `LAYER_MODEL_PATH`      | This is the Layer model path in form of `/[organization_name]/[project_name]/models/[model_name]`.       |
| `FEATURES` | These are the columns that this model requires to make a prediction. You should pass the columns as a list like `ARRAY[column1, column2, column3]`.        |


### AutoML

You can use any Layer ML model to make predictions with your dbt models.

_Syntax:_
```
layer.automl("MODEL_TYPE", ARRAY[FEATURES], TARGET)
```

_Parameters:_

| Syntax    | Description                                                                                                                                                                                                                                 |
| --------- |---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `MODEL_TYPE`    | Type of the model your want to train. There are two options: <br/> - `classifier`: A model to predict classes/labels or categories such as spam detection<br/>- `regressor`: A model to predict continious outcomes such as CLV prediction. |
| `FEATURES`    | Input column names as a list to train your AutoML model.                                                                                                                                                                                    |
| `TARGET`    | Target column that you want to predict.                                                                                                                                                                                                     |

