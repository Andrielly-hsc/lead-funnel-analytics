-- One row per lead: when and how fast it was first answered, and whether the SLA was met.
-- This is the single definition of "first response" and "SLA met" for the whole project.
with

leads as (
    select
        lead_id,
        created_at
    from {{ ref('stg_crm__leads') }}
),

interactions as (
    select
        lead_id,
        occurred_at
    from {{ ref('stg_crm__interactions') }}
),

first_contact as (
    select
        lead_id,
        min(occurred_at) as first_response_at
    from interactions
    group by lead_id
),

joined as (
    select
        leads.lead_id,
        first_contact.first_response_at,
        -- null (not zero!) when the lead was never answered
        date_diff('second', leads.created_at, first_contact.first_response_at)
        / 60.0 as minutes_to_first_response
    from leads
    left join first_contact
        on leads.lead_id = first_contact.lead_id
),

flagged as (
    select
        lead_id,
        first_response_at,
        minutes_to_first_response,
        first_response_at is not null as is_responded,
        -- first contact before the lead existed: clock skew, the duration is unknown
        coalesce(minutes_to_first_response < 0, false) as is_response_time_invalid,
        coalesce(
            minutes_to_first_response > {{ var('response_outlier_days') }} * 24 * 60, false
        ) as is_response_time_outlier
    from joined
),

final as (
    select
        *,
        case
            when not is_responded then false
            when is_response_time_invalid then null  -- unknown, not "met"
            else minutes_to_first_response <= {{ var('sla_minutes') }}
        end as is_sla_met
    from flagged
)

select * from final
