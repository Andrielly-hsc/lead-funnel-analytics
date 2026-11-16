# Data dictionary — synthetic CRM export

> **Generated from `src/lead_funnel/generator/schema.py` — do not edit by hand.**
> Regenerate with `python -m lead_funnel.generator.schema > docs/data/data_dictionary.md`.
> A unit test fails if this file and the code disagree.

All timestamps are **UTC** in ISO 8601. Business hours are defined in local time
(Europe/Berlin), so convert before analysing hour-of-day or weekday patterns.
All personal-looking data (e-mail, phone, company name) is **fictional**.


## `leads`

- **File:** `data/raw/leads.csv` (csv)
- **Grain:** One row per lead as exported by the CRM (the export may contain duplicates).
- **Primary key:** `lead_id`

| Column | Type | Nullable | Allowed values | Description |
|---|---|---|---|---|
| `lead_id` | string | no |  | CRM identifier of the lead, e.g. `L0000001`. |
| `created_at` | timestamp | no |  | When the lead entered the CRM (UTC). |
| `channel` | string | no | `web_form`, `email`, `phone`, `partner_referral` | How the lead reached us. |
| `source` | string | no | `organic_search`, `paid_search`, `social`, `event`, `partner`, `direct` | Marketing source of the lead. |
| `campaign_id` | string | yes |  | Campaign active at creation (paid, social, event). |
| `country` | string | no | `DE`, `AT`, `CH`, `NL`, `FR`, `IT`, `ES`, `PL`, `BE`, `DK` | ISO 3166-1 alpha-2 country code. |
| `industry` | string | yes | `manufacturing`, `retail`, `financial_services`, `healthcare`, `energy`, `automotive`, `logistics`, `it_services`, `public_sector`, `education` | Industry of the company. |
| `company_name` | string | no |  | Fictional company name. |
| `company_size` | integer | yes |  | Number of employees (self-reported). |
| `lead_score` | integer | no |  | Marketing lead score, 0-100 (higher = better). |
| `email` | string | no |  | Fake contact e-mail on a reserved `.example` domain. |
| `phone` | string | no |  | Fake contact phone number. |
| `owner_agent_id` | string | no |  | Agent the lead was routed to. |

## `interactions`

- **File:** `data/raw/interactions.jsonl` (jsonl)
- **Grain:** One row per outbound contact attempt by an agent.
- **Primary key:** `interaction_id`

| Column | Type | Nullable | Allowed values | Description |
|---|---|---|---|---|
| `interaction_id` | string | no |  | Identifier of the event, e.g. `I0000001`. |
| `lead_id` | string | no |  | Lead contacted. |
| `agent_id` | string | no |  | Agent who made the contact. |
| `event_type` | string | no | `call`, `email`, `meeting` | Kind of contact. |
| `occurred_at` | timestamp | no |  | When the contact happened (UTC). |
| `recorded_at` | timestamp | no |  | When the CRM stored the event (UTC). |
| `duration_s` | integer | no |  | Duration of the contact in seconds. |

## `agents`

- **File:** `data/raw/agents.parquet` (parquet)
- **Grain:** One row per agent *version*: a new row each time an agent changes team.
- **Primary key:** `agent_id, valid_from`

| Column | Type | Nullable | Allowed values | Description |
|---|---|---|---|---|
| `agent_id` | string | no |  | Agent identifier, e.g. `A001`. |
| `team` | string | no | `inbound_dach`, `inbound_international`, `partner`, `enterprise` | Team the agent belonged to in this period. |
| `seniority` | string | no | `junior`, `mid`, `senior` | Experience level. |
| `valid_from` | date | no |  | First day of this version (inclusive). |
| `valid_to` | date | yes |  | Last day of this version (exclusive); null = current. |

## `campaigns`

- **File:** `data/raw/campaigns.parquet` (parquet)
- **Grain:** One row per marketing campaign.
- **Primary key:** `campaign_id`

| Column | Type | Nullable | Allowed values | Description |
|---|---|---|---|---|
| `campaign_id` | string | no |  | Campaign identifier, e.g. `C001`. |
| `campaign_name` | string | no |  | Human-readable name. |
| `source` | string | no | `paid_search`, `social`, `event` | Marketing source. |
| `start_date` | date | no |  | First day (inclusive). |
| `end_date` | date | no |  | Last day (inclusive). |
| `budget_eur` | float | no |  | Planned budget in euros. |

## `opportunities`

- **File:** `data/raw/opportunities.csv` (csv)
- **Grain:** One row per opportunity created from a converted lead.
- **Primary key:** `opportunity_id`

| Column | Type | Nullable | Allowed values | Description |
|---|---|---|---|---|
| `opportunity_id` | string | no |  | Identifier, e.g. `O000001`. |
| `lead_id` | string | no |  | Lead that converted. |
| `opened_at` | timestamp | no |  | When the opportunity was opened (UTC). |
| `amount_eur` | float | no |  | Expected deal value in euros. |
