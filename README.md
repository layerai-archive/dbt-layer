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
        <img alt="License" src="https://img.shields.io/github/license/layerai/dbt-adapters.svg?color=blue">
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
- [Object detection in product images](https://github.com/layerai/examples-dbt/tree/main/cloth_detector) - Detects clothes from product images using a pre-trained computer vision model.
- [Review Scores Prediction with AutoML](https://github.com/layerai/dbt-layer/tree/main/examples/order_review_predictionr) - Train an AutoML model to predict the review scores.

## Quick Tour


### AutoML

You can automatically build state-of-the-art ML models using your own dbt models with plain SQL. To train an AutoML model all you have to do is pass your model type, input data (features) and target column you want to predict to `layer.automl()` in your SQL.

_Syntax:_
```
layer.automl("MODEL_TYPE", ARRAY[FEATURES], TARGET)
```

_Parameters:_

| Syntax    | Description                                                                                                                                                                                                                                 |
| --------- |---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `MODEL_TYPE`    | Type of the model your want to train. There are two options: <br/> <ul><li>`classifier`: A model to predict classes/labels or categories such as `spam, no-spam (ham)` in the classic spam detection model</li><li> `regressor`: A model to predict continuous outcomes such as a share price prediction.</li></ul> |
| `FEATURES`    | Input column names as a list to train your AutoML model.                                                                                                                                                                                    |
| `TARGET`    | Target column that you want to predict.                                                                                                                                                                                                     |


_Requirements:_
- For AutoML to work, you need to add  the configuration `layer_api_key` with the API key of your Layer account into your dbt profile .

_Example:_

Check out [Order Review AutoML Project](https://github.com/layerai/dbt-layer/tree/mecevit/update-docs/examples/order_review_prediction):

```sql
SELECT order_id,
       layer.automl(
           -- This is a regression problem
           'regressor',
           -- Data (input features) to train our model
           ARRAY[
           days_between_purchase_and_delivery, order_approved_late,
           actual_delivery_vs_expectation_bucket, total_order_price, total_order_freight, is_multiItems_order,seller_shipped_late],
           -- Target column we want to predict
           review_score
       )
FROM {{ ref('training_data') }}
```

### Prediction

You can run predictions using any Layer ML model with your dbt models. Layer dbt Adapter helps you score your data within your dbt DAG with SQL.

_Syntax:_
```
layer.predict("LAYER_MODEL_PATH", ARRAY[FEATURES])
```

_Parameters:_

| Syntax    | Description                                                                                                                                                                                        |
| --------- |----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `LAYER_MODEL_PATH`      | This is the Layer model path in form of `/[organization_name]/[project_name]/models/[model_name]`. You can use only the model name if you want to use an AutoML model within the same dbt project. |
| `FEATURES` | These are the columns that this model requires to make a prediction. You should pass the columns as a list like `ARRAY[column1, column2, column3]`.                                                |

_Example:_

Check out the [Cloth Detection Project](https://github.com/layerai/dbt-layer/tree/mecevit/update-docs/examples/cloth_detector):

```sql
SELECT
    id,
    layer.predict("layer/clothing/models/objectdetection", ARRAY[image])
FROM
    {{ ref("products") }}
```



## FAQ

1. Do I need a Layer account?
- If you want to use public models from [Layer](https://layer.ai) you don't. But if you want to create your own models with AutoML, you can always [create your free Layer account](https://app.layer.ai/login?returnTo=%2Fgetting-started).
2. How do I get my `layer-api-key`?
- First, [create your free Layer account](https://app.layer.ai/login?returnTo=%2Fgetting-started). 
- Go to [app.layer.ai](https://app.layer.ai) > **Settings** (Cog Icon by your profile photo) > **Developer** > **Create API key** to get your Layer API Key. 
