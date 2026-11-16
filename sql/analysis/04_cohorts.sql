-- Cohort analysis
-- Question: how quickly do leads convert, by the week or month they were created in?
-- Grain: one row per creation cohort. Author: Andrielly-hsc.
-- A cohort groups leads by creation period and follows them over time, so early and
-- late cohorts are compared at the same "age". Probable duplicates excluded (KI-01).
-- Caveat (right-censoring): in a live CRM the newest cohorts have not had time to
-- convert yet; compare cohorts only at ages every cohort has reached.

-- Q1: Weekly cohorts of Q1 2025: cumulative conversion by weeks since creation
with

leads as (
    select
        d.iso_year,
        d.iso_week,
        f.is_converted,
        floor(f.days_to_opportunity / 7) as weeks_to_opportunity
    from marts.fct_leads as f
    inner join marts.dim_date as d on f.created_date_key = d.date_key
    where not f.is_probable_duplicate and d.iso_year = 2025 and d.iso_week <= 13
)

select
    iso_week as cohort_week,
    count(*) as leads,
    round(count(*) filter (where weeks_to_opportunity <= 0) / count(*), 4) as conv_week_0,
    round(count(*) filter (where weeks_to_opportunity <= 1) / count(*), 4) as conv_week_1,
    round(count(*) filter (where weeks_to_opportunity <= 2) / count(*), 4) as conv_week_2,
    round(count(*) filter (where weeks_to_opportunity <= 4) / count(*), 4) as conv_week_4,
    round(count(*) filter (where is_converted) / count(*), 4) as conv_final
from leads
group by iso_week
order by iso_week;

-- Q2: Monthly cohorts: conversion and speed
with

leads as (
    select
        date_trunc('month', created_at_local) as cohort_month,
        is_converted,
        days_to_opportunity
    from marts.fct_leads
    where not is_probable_duplicate
)

select
    strftime(cohort_month, '%Y-%m') as cohort_month,
    count(*) as leads,
    round(avg(is_converted::int), 4) as conversion_rate,
    round(count(*) filter (where days_to_opportunity <= 7) / count(*), 4) as conv_within_7d,
    round(median(days_to_opportunity), 1) as median_days_to_opportunity
from leads
group by cohort_month
order by cohort_month;
