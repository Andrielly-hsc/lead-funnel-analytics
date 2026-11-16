-- Reconciliation: the fact must show exactly the opportunities of the source,
-- in number and in value. Returns a row only when they disagree.
with

fact as (
    select
        count(*) filter (where is_converted) as n_converted,
        coalesce(sum(opportunity_amount_eur), 0) as amount_eur
    from {{ ref('fct_leads') }}
),

source as (
    select
        count(*) as n_opportunities,
        coalesce(sum(amount_eur), 0) as amount_eur
    from {{ ref('stg_crm__opportunities') }}
)

select
    fact.n_converted,
    source.n_opportunities,
    fact.amount_eur as fact_amount_eur,
    source.amount_eur as source_amount_eur
from fact
cross join source
where
    fact.n_converted != source.n_opportunities
    or abs(fact.amount_eur - source.amount_eur) > 0.01
