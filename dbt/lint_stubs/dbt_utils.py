"""Lint-time stand-ins for dbt_utils macros (sqlfluff jinja templater ``library_path``).

sqlfluff does not run dbt, so package macros are unknown when linting. These
functions return *equivalent, parseable* SQL so the surrounding model can be linted.
They are never used by dbt itself.
"""


def generate_surrogate_key(field_list):
    return (
        "md5(" + " || '-' || ".join(f"coalesce(cast({f} as varchar), '')" for f in field_list) + ")"
    )


def date_spine(datepart, start_date, end_date):
    return (
        f"select cast(range as date) as date_{datepart} "
        f"from range({start_date}, {end_date}, interval 1 day)"
    )
