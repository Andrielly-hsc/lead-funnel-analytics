-- One row per lead: is it a probable duplicate of an earlier lead?
--
-- Rule (deterministic, chosen in F05-T04 from a precision/recall comparison):
--   two leads are the same person if they share the normalised e-mail OR the
--   normalised phone number (both compared as salted hashes).
-- The earliest lead of each group is the master; later ones point to it.
-- Fuzzy company-name matching is NOT used for automatic merging: it produced
-- too many false matches (see reports/quality/dedup_analysis.md).
with

leads as (
    select
        lead_id,
        created_at,
        email_hash,
        phone_hash
    from {{ ref('stg_crm__leads') }}
),

masters as (
    select
        lead_id,
        first_value(lead_id) over (
            partition by email_hash order by created_at, lead_id
        ) as email_master_id,
        first_value(lead_id) over (
            partition by phone_hash order by created_at, lead_id
        ) as phone_master_id
    from leads
),

final as (
    select
        lead_id,
        case
            when email_master_id != lead_id then email_master_id
            when phone_master_id != lead_id then phone_master_id
        end as duplicate_of_lead_id,
        case
            when email_master_id != lead_id then 'email'
            when phone_master_id != lead_id then 'phone'
        end as duplicate_match_key
    from masters
)

select
    lead_id,
    duplicate_of_lead_id,
    duplicate_match_key,
    duplicate_of_lead_id is not null as is_probable_duplicate
from final
