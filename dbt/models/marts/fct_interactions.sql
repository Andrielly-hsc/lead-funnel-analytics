-- Transaction fact. Grain: one row per interaction (outbound contact attempt).
with

interactions as (
    select * from {{ ref('stg_crm__interactions') }}
),

first_response as (
    select
        lead_id,
        first_response_at
    from {{ ref('int_leads__first_response') }}
),

dim_agent as (
    select * from {{ ref('dim_agent') }}
),

localised as (
    select
        *,
        timezone('{{ var("local_timezone") }}', occurred_at) as occurred_at_local
    from interactions
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['localised.interaction_id']) }} as interaction_key,
        localised.interaction_id,
        {{ dbt_utils.generate_surrogate_key(['localised.lead_id']) }} as lead_key,
        dim_agent.agent_key,
        cast(strftime(localised.occurred_at_local, '%Y%m%d') as integer) as event_date_key,
        localised.event_type,
        localised.occurred_at,
        localised.occurred_at_local,
        localised.recorded_at,
        localised.duration_s,
        localised.recording_lag_minutes,
        localised.recording_lag_minutes > {{ var('late_record_hours') }} * 60 as is_recorded_late,
        localised.occurred_at = first_response.first_response_at as is_first_touch
    from localised
    left join first_response
        on localised.lead_id = first_response.lead_id
    -- point-in-time join: the agent version valid on the (local) event date
    left join dim_agent
        on
            localised.agent_id = dim_agent.agent_id
            and cast(localised.occurred_at_local as date) >= dim_agent.valid_from
            and (
                dim_agent.valid_to is null
                or cast(localised.occurred_at_local as date) < dim_agent.valid_to
            )
)

select * from final
