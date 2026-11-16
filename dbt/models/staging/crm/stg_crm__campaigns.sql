with

source as (
    select * from {{ source('crm', 'campaigns') }}
),

renamed as (
    select
        campaign_id,
        campaign_name,
        lower(trim(source)) as lead_source,
        start_date,
        end_date,
        budget_eur,
        _loaded_at
    from source
)

select * from renamed
