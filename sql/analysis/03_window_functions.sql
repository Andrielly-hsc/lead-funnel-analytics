-- Window functions
-- Question: how do agents rank, how do rates evolve, how is effort spread over time?
-- Grain: see each query. Author: Andrielly-hsc.
-- Window functions compute a value per row from a "window" of related rows WITHOUT
-- collapsing the rows (unlike group by). Probable duplicates are excluded (KI-01).

-- Q1: Top 3 agents by SLA rate in each ISO week (weeks 10-12 of 2025)
-- dense_rank() ranks within each week; qualify filters on the window result, which a
-- where clause cannot do (where runs before windows are computed). Agents with fewer
-- than 20 leads in the week are excluded: a 100 % rate on 3 leads means little.
with

weekly as (
    select
        d.iso_year,
        d.iso_week,
        a.agent_id,
        count(*) as leads,
        avg(f.is_sla_met::int) as sla_rate
    from marts.fct_leads as f
    inner join marts.dim_date as d on f.created_date_key = d.date_key
    inner join marts.dim_agent as a on f.owner_agent_key = a.agent_key
    where not f.is_probable_duplicate and d.iso_year = 2025 and d.iso_week between 10 and 12
    group by all
    having count(*) >= 20
)

select
    iso_week,
    dense_rank() over (partition by iso_year, iso_week order by sla_rate desc) as rank_in_week,
    agent_id,
    leads,
    round(sla_rate, 4) as sla_rate
from weekly
qualify rank_in_week <= 3
order by iso_week, rank_in_week, agent_id;

-- Q2: Rolling 4-week conversion rate
-- Correct: ratio of rolling SUMS (conversions / leads over the window).
-- Wrong (shown for contrast): rolling AVERAGE of weekly rates, which gives a small
-- week the same weight as a large one.
with

weekly as (
    select
        d.iso_year,
        d.iso_week,
        count(*) as leads,
        count(*) filter (where f.is_converted) as conversions
    from marts.fct_leads as f
    inner join marts.dim_date as d on f.created_date_key = d.date_key
    where not f.is_probable_duplicate
    group by all
)

select
    iso_year,
    iso_week,
    leads,
    round(conversions / leads, 4) as weekly_rate,
    round(
        sum(conversions) over w4 / sum(leads) over w4, 4
    ) as rolling_4w_rate,
    round(avg(conversions / leads) over w4, 4) as rolling_avg_of_rates_wrong
from weekly
window w4 as (order by iso_year, iso_week rows between 3 preceding and current row)
order by iso_year, iso_week;

-- Q3: Days between consecutive touches, by touch number
-- lag() fetches the previous interaction of the same lead.
with

touches as (
    select
        lead_key,
        occurred_at,
        row_number() over (partition by lead_key order by occurred_at) as touch_number,
        date_diff(
            'minute',
            lag(occurred_at) over (partition by lead_key order by occurred_at),
            occurred_at
        ) / 1440.0 as days_since_previous
    from marts.fct_interactions
)

select
    touch_number,
    count(*) as touches,
    round(median(days_since_previous), 2) as median_days_since_previous,
    round(quantile_cont(days_since_previous, 0.9), 2) as p90_days_since_previous
from touches
where touch_number between 2 and 7
group by touch_number
order by touch_number;

-- Q4: Monthly pipeline value, running total and share of the year
-- sum() over (order by ...) = running total; sum() over () = grand total on every row.
with

monthly as (
    select
        date_trunc('month', opportunity_opened_at) as opened_month,
        count(*) as opportunities,
        sum(opportunity_amount_eur) as pipeline_eur
    from marts.fct_leads
    where is_converted and not is_probable_duplicate
    group by opened_month
)

select
    strftime(opened_month, '%Y-%m') as opened_month,
    opportunities,
    round(pipeline_eur, 0) as pipeline_eur,
    round(sum(pipeline_eur) over (order by opened_month), 0) as running_total_eur,
    round(pipeline_eur / sum(pipeline_eur) over (), 4) as share_of_total
from monthly
order by opened_month;

-- Q5: Each agent's SLA rate against their team's average
-- avg() over (partition by team) puts the team benchmark on every agent row.
with

per_agent as (
    select
        a.team,
        a.agent_id,
        count(*) as leads,
        avg(f.is_sla_met::int) as sla_rate
    from marts.fct_leads as f
    inner join marts.dim_agent as a on f.owner_agent_key = a.agent_key
    where not f.is_probable_duplicate
    group by all
)

select
    team,
    agent_id,
    leads,
    round(sla_rate, 4) as sla_rate,
    round(avg(sla_rate) over (partition by team), 4) as team_avg_sla_rate,
    round(sla_rate - avg(sla_rate) over (partition by team), 4) as diff_vs_team
from per_agent
order by team asc, diff_vs_team desc;
