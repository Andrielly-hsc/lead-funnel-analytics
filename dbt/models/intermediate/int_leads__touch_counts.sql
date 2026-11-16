-- One row per lead: how much effort agents put into it.
with

leads as (
    select lead_id from {{ ref('stg_crm__leads') }}
),

interactions as (
    select * from {{ ref('stg_crm__interactions') }}
),

per_lead as (
    select
        lead_id,
        count(*) as n_touches,
        count(*) filter (where event_type = 'call') as n_calls,
        count(*) filter (where event_type = 'email') as n_emails,
        count(*) filter (where event_type = 'meeting') as n_meetings,
        count(*) filter (
            where recording_lag_minutes > {{ var('late_record_hours') }} * 60
        ) as n_late_records,
        max(occurred_at) as last_touch_at
    from interactions
    group by lead_id
),

final as (
    select
        leads.lead_id,
        coalesce(per_lead.n_touches, 0) as n_touches,
        coalesce(per_lead.n_calls, 0) as n_calls,
        coalesce(per_lead.n_emails, 0) as n_emails,
        coalesce(per_lead.n_meetings, 0) as n_meetings,
        coalesce(per_lead.n_late_records, 0) as n_late_records,
        per_lead.last_touch_at
    from leads
    left join per_lead
        on leads.lead_id = per_lead.lead_id
)

select * from final
