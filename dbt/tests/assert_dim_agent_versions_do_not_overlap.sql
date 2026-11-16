-- SCD2 integrity: for each agent, versions are contiguous and never overlap.
-- Returns offending rows (a dbt singular test passes when it returns nothing).
with

versions as (
    select
        agent_id,
        valid_from,
        valid_to,
        lead(valid_from) over (partition by agent_id order by valid_from) as next_valid_from
    from {{ ref('dim_agent') }}
)

select *
from versions
where
    (next_valid_from is not null and valid_to is distinct from next_valid_from)
    or (next_valid_from is null and valid_to is not null)
