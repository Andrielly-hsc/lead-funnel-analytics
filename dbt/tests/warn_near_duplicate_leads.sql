-- WARN (known issue KI-01): the same person registered under several lead ids.
-- Accepted: kept as separate leads and flagged downstream (F05-T04).
{{ config(severity='warn', error_if='> 2500', store_failures=true) }}

select
    email_hash,
    count(*) as n_leads,
    min(lead_id) as first_lead_id,
    max(lead_id) as last_lead_id
from {{ ref('stg_crm__leads') }}
group by email_hash
having count(*) > 1
