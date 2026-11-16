-- SLA compliance
-- Question: where and when is the 60-minute first-response SLA missed?
-- Grain: fct_leads, one row per lead. Author: Andrielly-hsc.
-- Assumptions: probable duplicates excluded (KI-01); leads with invalid response
-- times have is_sla_met = null and drop out of avg() automatically (KI-02).

-- Q1: SLA rate by team and channel
-- Team = the owner's team *at the time the lead was created* (SCD2 point-in-time key).
select
    a.team,
    c.channel_label as channel,
    count(*) as leads,
    round(avg(f.is_sla_met::int), 4) as sla_rate,
    round(median(f.minutes_to_first_response), 1) as median_minutes
from marts.fct_leads as f
inner join marts.dim_agent as a on f.owner_agent_key = a.agent_key
inner join marts.dim_channel as c on f.channel_key = c.channel_key
where not f.is_probable_duplicate
group by a.team, c.channel_label
order by a.team, sla_rate;

-- Q2: Weekly SLA trend (ISO weeks)
-- Grouped by iso_year + iso_week: grouping by calendar year + iso_week would split
-- ISO week 1 of 2026, which starts on 2025-12-29.
select
    d.iso_year,
    d.iso_week,
    min(d.date_day) as week_start,
    count(*) as leads,
    round(avg(f.is_sla_met::int), 4) as sla_rate
from marts.fct_leads as f
inner join marts.dim_date as d on f.created_date_key = d.date_key
where not f.is_probable_duplicate
group by d.iso_year, d.iso_week
order by d.iso_year, d.iso_week;

-- Q3: SLA rate by local hour of creation
-- Leads created after 18:00 wait for the next business opening (08:00 local time),
-- so the SLA is structurally out of reach for them. Uses local time, not UTC.
select
    hour(f.created_at_local) as local_hour,
    count(*) as leads,
    round(avg(f.is_sla_met::int), 4) as sla_rate,
    round(median(f.minutes_to_first_response) / 60, 1) as median_hours_to_response
from marts.fct_leads as f
where not f.is_probable_duplicate
group by local_hour
order by local_hour;
