with

sources as (
    select distinct lead_source from {{ ref('stg_crm__leads') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['lead_source']) }} as lead_source_key,
        lead_source,
        replace(upper(left(lead_source, 1)) || substr(lead_source, 2), '_', ' ')
            as lead_source_label,
        lead_source in ('paid_search', 'social') as is_paid_media,
        lead_source in ('paid_search', 'social', 'event') as has_campaigns
    from sources
)

select * from final
