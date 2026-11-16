{% docs lead_id %}
Natural key of the lead in the CRM, e.g. `L0000001`.
{% enddocs %}

{% docs agent_id %}
Natural key of the agent, stable across team changes, e.g. `A001`.
{% enddocs %}

{% docs interaction_id %}
Natural key of the interaction in the CRM, e.g. `I0000001`.
{% enddocs %}

{% docs opportunity_id %}
Natural key of the opportunity, e.g. `O000001`.
{% enddocs %}

{% docs campaign_id %}
Natural key of the marketing campaign, e.g. `C001`.
{% enddocs %}

{% docs loaded_at %}
When `lead-funnel ingest` loaded this row into the raw layer (UTC). Used for
source freshness checks and deduplication (latest load wins).
{% enddocs %}

{% docs surrogate_key %}
Surrogate key: MD5 hash of the natural key, generated with
`dbt_utils.generate_surrogate_key`. Used for joins between facts and dimensions.
{% enddocs %}

{% docs team %}
Support team: `inbound_dach`, `inbound_international`, `partner` or `enterprise`.
{% enddocs %}

{% docs seniority %}
Experience level of the agent: `junior`, `mid` or `senior`.
{% enddocs %}

{% docs valid_from %}
First day this version of the record is valid (inclusive).
{% enddocs %}

{% docs valid_to %}
Day this version stops being valid (exclusive). Null for the current version.
{% enddocs %}

{% docs is_current %}
True for the version that is valid today (`valid_to` is null).
{% enddocs %}

{% docs event_type %}
Kind of outbound contact: `call`, `email` or `meeting`.
{% enddocs %}

{% docs duration_s %}
Duration of the contact in seconds.
{% enddocs %}

{% docs lead_source %}
Marketing source of the lead: `organic_search`, `paid_search`, `social`, `event`,
`partner` or `direct`.
{% enddocs %}

{% docs is_responded %}
True if the lead received at least one outbound interaction.
{% enddocs %}

{% docs is_sla_met %}
**Business rule (single definition):** true if the first response arrived within
`var('sla_minutes')` minutes (default 60) of lead creation. False for leads never
answered. Null only when the response time is invalid (first contact recorded
before the lead existed), because the real duration is unknown.
{% enddocs %}

{% docs minutes_to_first_response %}
Minutes from lead creation to the first outbound interaction. **Null (not zero)**
when the lead was never answered: averaging zeros would make the team look faster
than it is. Negative values are clock-skew errors, flagged by
`is_response_time_invalid`.
{% enddocs %}

{% docs n_touches %}
Number of outbound interactions with the lead (calls + e-mails + meetings).
{% enddocs %}

{% docs amount_eur %}
Expected deal value of the opportunity in euros.
{% enddocs %}
