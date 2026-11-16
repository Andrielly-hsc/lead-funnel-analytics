{#-
    Use the custom schema name as-is (staging, intermediate, marts, reference)
    instead of dbt's default "<target_schema>_<custom_schema>" (e.g. main_staging).
    Clean names are easier to query for analysts and BI tools.
-#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
