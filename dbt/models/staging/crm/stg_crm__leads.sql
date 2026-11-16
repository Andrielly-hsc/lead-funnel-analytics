-- One row per lead_id: cleaned, standardised and pseudonymised.
-- Exact duplicates (same row exported twice) are removed here.
-- Near-duplicates (same person, new lead_id) are kept and analysed in F05.
with

source as (
    select * from {{ source('crm', 'leads') }}
),

channel_mapping as (
    select * from {{ ref('channel_mapping') }}
),

country_mapping as (
    select * from {{ ref('country_mapping') }}
),

renamed as (
    select
        lead_id,
        created_at,
        timezone('{{ var("local_timezone") }}', created_at) as created_at_local,
        lower(trim(channel)) as channel_raw,
        lower(trim(source)) as lead_source,
        campaign_id,
        lower(trim(country)) as country_raw,
        industry,
        trim(company_name) as company_name,
        company_size,
        lead_score,
        lower(trim(email)) as email_normalised,
        -- digits only, international prefix "00" removed: "0049-30-123" == "+49 30 123"
        regexp_replace(regexp_replace(phone, '[^0-9]', '', 'g'), '^00', '') as phone_normalised,
        owner_agent_id,
        _loaded_at
    from source
),

standardised as (
    select
        renamed.lead_id,
        renamed.created_at,
        renamed.created_at_local,
        coalesce(channel_mapping.channel, renamed.channel_raw) as channel,
        renamed.lead_source,
        renamed.campaign_id,
        coalesce(country_mapping.country_code, upper(renamed.country_raw)) as country_code,
        renamed.industry,
        renamed.company_name,
        renamed.company_size,
        case
            when renamed.company_size is null then 'unknown'
            when renamed.company_size < 50 then 'small'
            when renamed.company_size < 250 then 'medium'
            when renamed.company_size < 1000 then 'large'
            else 'enterprise'
        end as company_size_band,
        renamed.lead_score,
        {{ pseudonymise('renamed.email_normalised') }} as email_hash,
        {{ pseudonymise('renamed.phone_normalised') }} as phone_hash,
        renamed.owner_agent_id,
        renamed._loaded_at
    from renamed
    left join channel_mapping
        on renamed.channel_raw = channel_mapping.raw_value
    left join country_mapping
        on renamed.country_raw = country_mapping.raw_value
),

deduplicated as (
    select *
    from standardised
    qualify row_number() over (partition by lead_id order by _loaded_at desc) = 1
)

select * from deduplicated
