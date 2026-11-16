-- ERROR (consistency across tables): an opportunity cannot exist before its lead.
select
    opportunities.opportunity_id,
    opportunities.opened_at,
    leads.created_at
from {{ ref('stg_crm__opportunities') }} as opportunities
inner join {{ ref('stg_crm__leads') }} as leads
    on opportunities.lead_id = leads.lead_id
where opportunities.opened_at < leads.created_at
