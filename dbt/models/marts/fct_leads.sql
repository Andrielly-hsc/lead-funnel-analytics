-- Accumulating snapshot fact. Grain: one row per lead.
-- Each milestone of the lead lifecycle (created -> first response -> opportunity)
-- is a column, so funnel and SLA metrics need no further joins.
with

leads as (
    select * from {{ ref('stg_crm__leads') }}
),

first_response as (
    select * from {{ ref('int_leads__first_response') }}
),

touches as (
    select * from {{ ref('int_leads__touch_counts') }}
),

duplicates as (
    select * from {{ ref('int_leads__duplicates') }}
),

opportunities as (
    select * from {{ ref('stg_crm__opportunities') }}
),

dim_agent as (
    select * from {{ ref('dim_agent') }}
),

dim_channel as (
    select * from {{ ref('dim_channel') }}
),

dim_lead_source as (
    select * from {{ ref('dim_lead_source') }}
),

dim_campaign as (
    select * from {{ ref('dim_campaign') }}
),

final as (
    select
        -- keys
        {{ dbt_utils.generate_surrogate_key(['leads.lead_id']) }} as lead_key,
        leads.lead_id,
        cast(strftime(leads.created_at_local, '%Y%m%d') as integer) as created_date_key,
        dim_channel.channel_key,
        dim_lead_source.lead_source_key,
        coalesce(dim_campaign.campaign_key, '-1') as campaign_key,
        dim_agent.agent_key as owner_agent_key,

        -- lead attributes (low-cardinality codes kept on the fact for convenience)
        leads.country_code,
        leads.industry,
        leads.company_size,
        leads.company_size_band,
        leads.lead_score,
        leads.email_hash,

        -- milestones
        leads.created_at,
        leads.created_at_local,
        first_response.first_response_at,
        opportunities.opened_at as opportunity_opened_at,

        -- response measures and flags
        first_response.minutes_to_first_response,
        first_response.is_responded,
        first_response.is_sla_met,
        first_response.is_response_time_invalid,
        first_response.is_response_time_outlier,

        -- activity
        touches.n_touches,
        touches.n_calls,
        touches.n_emails,
        touches.n_meetings,
        touches.n_late_records,

        -- data quality
        duplicates.is_probable_duplicate,
        duplicates.duplicate_of_lead_id,

        -- outcome
        opportunities.opportunity_id is not null as is_converted,
        opportunities.opportunity_id,
        opportunities.amount_eur as opportunity_amount_eur,
        date_diff('second', leads.created_at, opportunities.opened_at)
        / 86400.0 as days_to_opportunity

    from leads
    left join first_response
        on leads.lead_id = first_response.lead_id
    left join touches
        on leads.lead_id = touches.lead_id
    left join duplicates
        on leads.lead_id = duplicates.lead_id
    left join opportunities
        on leads.lead_id = opportunities.lead_id
    left join dim_channel
        on leads.channel = dim_channel.channel
    left join dim_lead_source
        on leads.lead_source = dim_lead_source.lead_source
    left join dim_campaign
        on leads.campaign_id = dim_campaign.campaign_id
    -- point-in-time join: the agent version valid on the (local) creation date
    left join dim_agent
        on
            leads.owner_agent_id = dim_agent.agent_id
            and cast(leads.created_at_local as date) >= dim_agent.valid_from
            and (
                dim_agent.valid_to is null
                or cast(leads.created_at_local as date) < dim_agent.valid_to
            )
)

select * from final
