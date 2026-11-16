-- One row per agent version. The source already keeps team history
-- (valid_from inclusive, valid_to exclusive; null = current version).
with

source as (
    select * from {{ source('crm', 'agents') }}
),

renamed as (
    select
        agent_id,
        lower(trim(team)) as team,
        lower(trim(seniority)) as seniority,
        valid_from,
        valid_to,
        valid_to is null as is_current,
        _loaded_at
    from source
)

select * from renamed
