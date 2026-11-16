-- WARN (known issue KI-03): first response later than var('response_outlier_days')
-- days, most likely a wrong import date. Accepted: flagged; analyses decide.
{{ config(severity='warn', error_if='> 1000', store_failures=true) }}

select
    lead_id,
    created_at,
    first_response_at,
    minutes_to_first_response / 60 / 24 as days_to_first_response
from {{ ref('fct_leads') }}
where is_response_time_outlier
