-- SCD type 2: one row per agent version. Facts join on the version valid at the
-- time of the event, so history is never rewritten when an agent changes team.
with

agents as (
    select * from {{ ref('stg_crm__agents') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['agent_id', 'valid_from']) }} as agent_key,
        agent_id,
        team,
        seniority,
        valid_from,
        valid_to,
        is_current
    from agents
)

select * from final
