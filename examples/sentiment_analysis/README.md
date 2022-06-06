# Applying Sentiment Analysis in the dbt DAG

In this example, we show you how to make multi-language sentiment analysis from within a dbt pipeline, using a simple sql expression like this:

```sql
select id,
       review,
       layer.predict("layer/nlptown/models/sentimentanalysis", ARRAY[review])
from {{ref('reviews')}}
```

We use the [layer-dbt-adapter](https://github.com/layerai/dbt-adapters) to enable the `layer.predict` function. With `layer.predict`, we can load and apply a pre-trained machine learning model to data within a dbt pipeline. 
This ML-enabled stage becomes part of the dbt execution DAG. 


## How to run

First, install the open-source [Layer DBT Adapter](https://github.com/layerai/dbt-adapters). Currently, we only support BigQuery (more to come soon)

```shell
pip install dbt-layer-bigquery -U -q
```

Next, install the required libraries. This ML model is a finetuned Pytorch model open-sourced by [NLPTown](https://www.nlp.town/). So, we need some additional libraries for Pytorch.

```shell
pip install torch torchvision
```

Then, add a new BigQuery profile to your [DBT profile](https://docs.getdbt.com/dbt-cli/configure-your-profile/). Name it as `layer-profile`, and don't forget to set `type: layer_bigquery` for the Layer adapter to work. 
Here is a sample profile:


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
```

Now, are are ready to clone this repo and get to the folder for this example:
```shell
git clone https://github.com/layerai/examples-dbt
cd examples-dbt/sentiment_analysis
```

The example includes a sample dataset. 
You can seed the sample data [reviews table](seeds/reviews.csv) to your DWH.
The dataset includes a sample of multi-language product reviews from Amazon.

```shell
dbt seed
```

Finally, you can run the dbt project:

```shell
dbt run
```

When the project runs, the [layer-dbt-adapter](https://github.com/layerai/dbt-adapters) fetches the review text from the `ref('products')` relation and applies the sentiment model, producing a prediction score from 1 to 5 (1- lowest negative sentiment, 5- highest positive sentiment).

The application of the `layer.predict` function results in a column named `prediction`containing the predicted score for each row of the input dataset.
In this dbt pipeline, the resulting dataset is written back to the DWH, resulting in a new table with the scored data.


## Machine Learning Model

In this dbt example, we use a Bert model finetuned on product reviews in six languages: English, Dutch, German, French, Spanish, and Italian. It predicts the sentiment of the review as a number of stars (between 1 and 5).

This model is intended for direct use as a sentiment analysis model for product reviews in any of the six languages above, or for further finetuning on related sentiment analysis tasks.

To learn more about this machine learning model, visit:

https://app.layer.ai/layer/nlptown
