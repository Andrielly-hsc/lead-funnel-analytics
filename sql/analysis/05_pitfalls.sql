-- SQL pitfalls: wrong vs right
-- Question: which common query mistakes silently produce wrong numbers on this data?
-- Grain: each query returns ONE row with the wrong and the right result side by side.
-- None of these mistakes raises an error; that is what makes them dangerous.
-- Author: Andrielly-hsc. Explanations: docs/sql_pitfalls.md.

-- P1: Null is not zero (average response time)
-- Never-answered leads have a null response time. Replacing null with 0 counts them as
-- "answered instantly" and makes the team look faster.
select
    round(avg(coalesce(minutes_to_first_response, 0)), 1) as wrong_avg_minutes,
    round(avg(minutes_to_first_response), 1) as right_avg_minutes
from marts.fct_leads
where not is_probable_duplicate and not is_response_time_invalid;

-- P2: count(*) vs count(column) vs count(distinct column)
-- count(*) counts rows; count(col) skips nulls; count(distinct col) also skips nulls.
-- "How many leads have an industry?" is count(industry), not count(*).
select
    count(*) as wrong_leads_with_industry,
    count(industry) as right_leads_with_industry,
    count(distinct industry) as distinct_industries_null_excluded
from marts.fct_leads
where not is_probable_duplicate;

-- P3: NOT IN with a null in the subquery returns nothing
-- Question: how many leads are NOT the master of a duplicate group?
-- duplicate_of_lead_id is null for most leads. "x not in (..., null)" is never true
-- (it is null), so the NOT IN version returns 0. NOT EXISTS handles nulls correctly.
select
    (
        select count(*)
        from marts.fct_leads as f
        where f.lead_id not in (select g.duplicate_of_lead_id from marts.fct_leads as g)
    ) as wrong_not_in,
    (
        select count(*)
        from marts.fct_leads as f
        where not exists (
            select 1
            from marts.fct_leads as g
            where g.duplicate_of_lead_id = f.lead_id
        )
    ) as right_not_exists;

-- P4: Join fan-out inflates sums
-- Joining leads (1 row per lead) to interactions (n rows per lead) repeats each
-- opportunity amount once per interaction. Aggregate at the right grain first.
select
    (
        select round(sum(f.opportunity_amount_eur), 0)
        from marts.fct_leads as f
        inner join marts.fct_interactions as i on f.lead_key = i.lead_key
        where not f.is_probable_duplicate
    ) as wrong_pipeline_eur,
    (
        select round(sum(opportunity_amount_eur), 0)
        from marts.fct_leads
        where not is_probable_duplicate
    ) as right_pipeline_eur;

-- P5: Average of averages
-- Averaging per-channel conversion rates gives every channel the same weight, however
-- many leads it has. The overall rate must be computed from the underlying counts.
with

per_channel as (
    select
        channel_key,
        avg(is_converted::int) as rate
    from marts.fct_leads
    where not is_probable_duplicate
    group by channel_key
)

select
    round((select avg(per_channel.rate) from per_channel), 4) as wrong_avg_of_channel_rates,
    round(avg(is_converted::int), 4) as right_overall_rate
from marts.fct_leads
where not is_probable_duplicate;

-- P6: Time zones (business hours in UTC vs local time)
-- Timestamps are stored in UTC; business hours (08:00-18:00) are local (Europe/Berlin,
-- UTC+1 or +2). Using the UTC hour misclassifies leads around opening and closing.
select
    round(
        avg((hour(created_at) between 8 and 17 and isodow(created_at) <= 5)::int), 4
    ) as wrong_share_business_hours_utc,
    round(
        avg((hour(created_at_local) between 8 and 17 and isodow(created_at_local) <= 5)::int), 4
    ) as right_share_business_hours_local
from marts.fct_leads
where not is_probable_duplicate;

-- P7: Forgetting known duplicates
-- Duplicate leads are never contacted, so including them understates the response rate.
select
    round(avg(is_responded::int), 4) as wrong_response_rate_all_rows,
    round(avg(is_responded::int) filter (where not is_probable_duplicate), 4)
        as right_response_rate_deduplicated
from marts.fct_leads;

-- P8: Inequality filters silently drop nulls
-- "Leads not in retail": industry != 'retail' is null (not true) when industry is null,
-- so leads with an unknown industry vanish. Use "is distinct from" if they belong in.
select
    count(*) filter (where industry != 'retail') as wrong_not_retail,
    count(*) filter (where industry is distinct from 'retail') as right_not_retail
from marts.fct_leads
where not is_probable_duplicate;

-- P9: Integer division is not portable
-- DuckDB's "/" always returns a decimal; PostgreSQL and SQL Server truncate 7 / 2 to 3.
-- Ratios of counts must cast explicitly to stay correct on every engine. The ANSI
-- cast() syntax is used on purpose (the "::" shorthand is not portable either).
select
    7 // 2 as integer_division_like_postgres,
    7 / 2 as duckdb_division,
    cast(7 as double) / 2 as portable_division;  -- noqa: CV11
