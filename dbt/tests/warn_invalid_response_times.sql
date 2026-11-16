-- WARN (known issue KI-02): first contact recorded before the lead was created
-- (clock skew). Accepted: flagged and excluded from response-time metrics.
{{ config(severity='warn', error_if='> 1000', store_failures=true) }}

select
    lead_id,
    created_at,
    first_response_at,
    minutes_to_first_response
from {{ ref('fct_leads') }}
where is_response_time_invalid
