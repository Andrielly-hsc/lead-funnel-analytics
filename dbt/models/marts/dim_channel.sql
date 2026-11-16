with

channels as (
    select distinct channel from {{ ref('channel_mapping') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['channel']) }} as channel_key,
        channel,
        case channel
            when 'web_form' then 'Web form'
            when 'email' then 'E-mail'
            when 'phone' then 'Phone'
            when 'partner_referral' then 'Partner referral'
        end as channel_label
    from channels
)

select * from final
