
{% macro dbt-layer-bigquery__get_catalog(information_schema, schemas) -%}

  {% set msg -%}
    get_catalog not implemented for dbt-layer-bigquery
  {%- endset %}

  {{ exceptions.raise_compiler_error(msg) }}
{% endmacro %}
