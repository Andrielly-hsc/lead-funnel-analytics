-- One row per interaction_id, typed and renamed.
with

source as (
    select * from {{ source('crm', 'interactions') }}
),

renamed as (
    select
        interaction_id,
        lead_id,
        agent_id,
        lower(trim(event_type)) as event_type,
        occurred_at,
        recorded_at,
        duration_s,
        date_diff('second', occurred_at, recorded_at) / 60.0 as recording_lag_minutes,
        _loaded_at
    from source
),

deduplicated as (
    select *
    from renamed
    qualify row_number() over (partition by interaction_id order by _loaded_at desc) = 1
)

select * from deduplicated
