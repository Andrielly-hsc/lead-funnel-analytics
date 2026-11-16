-- WARN (known issue KI-04): interactions stored in the CRM more than
-- var('late_record_hours') after they happened (timeliness). Accepted: the
-- occurrence time is still correct; only near-real-time reports are affected.
{{ config(severity='warn', error_if='> 10000', store_failures=true) }}

select
    interaction_id,
    occurred_at,
    recorded_at,
    recording_lag_minutes
from {{ ref('fct_interactions') }}
where is_recorded_late
