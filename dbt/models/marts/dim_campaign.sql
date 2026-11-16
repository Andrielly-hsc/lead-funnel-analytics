-- One row per campaign plus a "No campaign" member (key '-1'), so the campaign
-- foreign key in facts is never null (Kimball: avoid null foreign keys).
with

campaigns as (
    select * from {{ ref('stg_crm__campaigns') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['campaign_id']) }} as campaign_key,
        campaign_id,
        campaign_name,
        lead_source,
        start_date,
        end_date,
        date_diff('day', start_date, end_date) + 1 as duration_days,
        budget_eur
    from campaigns

    union all

    select
        '-1' as campaign_key,
        null as campaign_id,
        'No campaign' as campaign_name,
        null as lead_source,
        null as start_date,
        null as end_date,
        null as duration_days,
        null as budget_eur
)

select * from final
