-- Calendar dimension, one row per day. Conformed: shared by every fact.
with

spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2024-01-01' as date)",
        end_date="cast('2027-01-01' as date)"
    ) }}
),

final as (
    select
        cast(strftime(date_day, '%Y%m%d') as integer) as date_key,
        cast(date_day as date) as date_day,
        year(date_day) as calendar_year,
        quarter(date_day) as calendar_quarter,
        month(date_day) as month_of_year,
        strftime(date_day, '%B') as month_name,
        isoyear(date_day) as iso_year,
        weekofyear(date_day) as iso_week,
        isodow(date_day) as iso_day_of_week,
        strftime(date_day, '%A') as day_name,
        isodow(date_day) >= 6 as is_weekend
    from spine
)

select * from final
