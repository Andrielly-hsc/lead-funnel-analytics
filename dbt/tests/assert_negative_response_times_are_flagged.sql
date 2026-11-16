-- ERROR: every negative response time must carry the invalid flag,
-- otherwise it would silently enter averages and SLA rates.
select
    lead_id,
    minutes_to_first_response,
    is_response_time_invalid
from {{ ref('fct_leads') }}
where minutes_to_first_response < 0 and not is_response_time_invalid
