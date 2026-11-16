-- Funnel KPIs
-- Question: how does the lead funnel perform overall and by channel?
-- Grain: fct_leads, one row per lead. Author: Andrielly-hsc.
-- Assumptions: probable duplicates are excluded (KNOWN ISSUE KI-01);
-- response-time statistics use valid response times only (KI-02);
-- SLA = first response within 60 minutes (var sla_minutes in dbt).

-- Q1: Overall KPIs
-- One row. `filter (where ...)` computes conditional aggregates in a single scan.
with

leads as (
    select * from marts.fct_leads
    where not is_probable_duplicate
)

select
    count(*) as leads,
    round(avg(is_responded::int), 4) as response_rate,
    round(avg(is_sla_met::int), 4) as sla_rate,
    round(
        median(minutes_to_first_response) filter (where not is_response_time_invalid), 1
    ) as median_minutes_to_response,
    round(
        quantile_cont(minutes_to_first_response, 0.9)
        filter (where not is_response_time_invalid),
        1
    ) as p90_minutes_to_response,
    round(avg(is_converted::int), 4) as conversion_rate,
    round(sum(opportunity_amount_eur), 0) as pipeline_value_eur
from leads;

-- Q2: KPIs by channel, with a grand total
-- `group by rollup (...)` adds the total row (channel = null) without a second query.
with

leads as (
    select
        f.*,
        c.channel_label
    from marts.fct_leads as f
    inner join marts.dim_channel as c on f.channel_key = c.channel_key
    where not f.is_probable_duplicate
)

select
    coalesce(channel_label, 'Total') as channel,
    count(*) as leads,
    round(avg(is_sla_met::int), 4) as sla_rate,
    round(median(minutes_to_first_response) filter (where not is_response_time_invalid), 1)
        as median_minutes_to_response,
    round(avg(is_converted::int), 4) as conversion_rate,
    round(avg(opportunity_amount_eur), 0) as avg_deal_eur
from leads
group by rollup (channel_label)
order by grouping(channel_label), leads desc;

-- Q3: Funnel stages with step and cumulative conversion
-- Stages must be NESTED subsets: each stage counts only leads that also passed every
-- previous stage. Counting each event independently made "converted" larger than
-- "meeting held" (step conversion > 100 %), because some leads converted without ever
-- being answered (see Q4).
with

leads as (
    select * from marts.fct_leads
    where not is_probable_duplicate
),

counts as (
    select
        count(*) as created,
        count(*) filter (where is_responded) as responded,
        count(*) filter (where is_responded and n_meetings > 0) as meeting_held,
        count(*) filter (
            where is_responded and n_meetings > 0 and is_converted
        ) as converted
    from leads
),

stages as (
    select
        1 as step,
        'created' as funnel_stage,
        created as leads
    from counts
    union all
    select
        2 as step,
        'responded' as funnel_stage,
        responded as leads
    from counts
    union all
    select
        3 as step,
        'meeting held' as funnel_stage,
        meeting_held as leads
    from counts
    union all
    select
        4 as step,
        'converted' as funnel_stage,
        converted as leads
    from counts
)

select
    step,
    funnel_stage,
    leads,
    round(leads / lag(leads) over (order by step), 4) as step_conversion,
    round(leads / first_value(leads) over (order by step), 4) as cumulative_conversion
from stages
order by step;

-- Q4: Leads that skipped funnel stages
-- Converted leads that were never answered or had no meeting. Small, but they explain
-- why a non-nested funnel shows impossible step rates; they need a business explanation
-- (e.g. a partner closed the deal directly).
select
    is_responded,
    n_meetings > 0 as had_meeting,
    count(*) as converted_leads
from marts.fct_leads
where is_converted and not is_probable_duplicate
group by all
order by converted_leads desc;
