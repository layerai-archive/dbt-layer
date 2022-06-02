<p align="center">
    <br>
    <a href="https://layer.ai">
          <img src="https://app.layer.ai/assets/layer_wordmark_black.png" width="40%"
alt="Layer"/>
    </a>
    <br>
</p>

<p align="center">
    <a href="https://pypi.python.org/pypi/dbt-layer-big
query">
        <img alt="PyPI" src="https://img.shields.io/pypi/v/layer.svg">
    </a>
</p>

# Layer dbt Adapter for BigQuery

This adapter runs ML pipelines inside dbt dag with BigQuery as the backing data warehouse. With Layer dbt Adapter you can:

- Score your data with a machine learning model from Layer
- Train an AutoML model with your data [coming soon...]
- Train a custom machine learning model with your data [coming soon...]

To learn more about Layer:

https://layer.ai

## Getting started
To start immediately using Layer inside your dbt dag, install Layer dbt Adapter:
```shell
pip install dbt-layer-bigquery -U
```

Add Layer dbt Adapter to your BigQuery profile. An example profile:
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

Now, start making predictions in your dbt dag:

```sql
select id,
       review,
       layer.predict("layer/nlptown/models/sentimentanalysis", ARRAY[review])
from {{ref('reviews')}}
```

## Examples
Check out the examples we have prepared for you:

- [Predicting survials of Titanic](https://github.com/layerai/examples-dbt/tree/main/titanic)
- [Sentiment analysis of product reviews](https://github.com/layerai/examples-dbt/tree/main/sentiment_analysis)
- [Object detection in product images](https://github.com/layerai/examples-dbt/tree/main/cloth_detector)

## Contributing

At Layer, our mission is to make machine learning more accessible. This opensource project is one of our initiatives to contribute to ML's growth and evolution. Help us with your contributions!

### Prerequisites
- `pyenv`
- `poetry`
- `make`

### Setup
Run `pyenv install` in the root of this repo to ensure you have the preferred Python version setup

### Makefile
We use `make` as our build system.

Targets:
- `install` - prepares the `poetry` virtual environment. Most of the other tasks will do that automatically for you
- `format` - formats the code
- `test` - runs unit tests
- `lint` - runs linters
- `check` - runs `test` and `lint`
- `publish` - publishes the project to PyPi. This is intended to be used in CI only.
- `clean` - cleans the repo, including the `poetry` virtual environment
- `help` - prints all targets

### Dependency management
The `poetry` documentation about dependency management is [here](https://python-poetry.org/docs/dependency-specification/)

Every time you change dependencies, you should expect a corresponding change to `poetry.lock`. If you use `poetry` directly, it will be done automatically for you. If you manually edit `pyproject.toml`, you need to run `poetry lock` after

### A few tips:
#### How to add a new dependency
```
    poetry add foo
    # or
    poetry add foo=="1.2.3"
```

#### How to add a new dev dependency
```
    poetry add foo --dev
    # or
    poetry add foo=="1.2.3" --dev
```

#### How to get an environment with this package and all dependencies
```
    poetry shell
```

#### How to run something inside the poetry environment
```
    poetry run <...>
```

#### How to update a dependency
```
    poetry update foo
```
