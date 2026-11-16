with

source as (
    select * from {{ source('crm', 'opportunities') }}
),

renamed as (
    select
        opportunity_id,
        lead_id,
        opened_at,
        amount_eur,
        _loaded_at
    from source
),

deduplicated as (
    select *
    from renamed
    qualify row_number() over (partition by opportunity_id order by _loaded_at desc) = 1
)

select * from deduplicated
