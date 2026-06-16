# Citeline API Documentation

> **Informa / Citeline**: The Citeline API is the data platform for Informa's pharma and life-sciences databases, covering Pharmaprojects, Trialtrove, Sitetrove, Biomedtracker (BMT), Meddevicetracker (MDT), and more. All access is via `https://api.citeline.com`.

---

## Authorization

### Preferred Method: Email/Password → Bearer Token

The API uses short-lived JWT Bearer tokens obtained by exchanging email/password credentials. Tokens expire in **24 hours** (`expires_in: 86400`).

**Step 1 — Obtain a token**

```
POST https://api.citeline.com/token
Content-Type: application/json

{
    "email": "example.user@citeline.com",
    "password": "MySecurePassw0rd?"
}
```

Response:
```json
{
    "access_token": "<jwt_token>",
    "expires_in": 86400,
    "token_type": "Bearer"
}
```

**Step 2 — Use the token on every request**

```
Authorization: Bearer <access_token>
```

The Swagger security definition confirms the header name is `Authorization` and the value format is `Bearer <token>`.

**Python example:**
```python
import requests

def get_token(email, password):
    resp = requests.post(
        "https://api.citeline.com/token",
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"},
    )
    resp.raise_for_status()
    data = resp.json()
    return f"Bearer {data['access_token']}"
```

**Connection parameters for the connector:**
- `email` (string, required) — registered Citeline account email
- `password` (string, required, secret) — account password

> Note: The connector stores `email` and `password`, fetches a fresh token at runtime, and attaches `Authorization: Bearer <token>` to every API call. Tokens should be re-fetched before expiry (24 h).

---

## Object List

The object list is **static** — the API provides a fixed set of resources. All resources are accessed under `https://api.citeline.com`. There is no discovery endpoint that enumerates available resources dynamically.

The API exposes resources across six product lines:

### Core Feed Resources (accessible via `/v1/feed/{resource}`)

| Resource path | Product | Description |
|---|---|---|
| `drug` | Citeline / Pharmaprojects | Drug information |
| `drug/trends` | Citeline / Pharmaprojects | Drug Trends View |
| `drug/program` | Citeline / Pharmaprojects | Drug program information |
| `drug/company` | Citeline / Pharmaprojects | Company drug associations |
| `drug/program/aggregation/company` | Citeline / Pharmaprojects | Drug programs aggregated by company |
| `drug/program/aggregation/company/country` | Citeline / Pharmaprojects | Drug programs by company/country |
| `drug/program/aggregation/country` | Citeline / Pharmaprojects | Drug programs aggregated by country |
| `drug/program/aggregation/country/company` | Citeline / Pharmaprojects | Drug programs by country/company |
| `drug/program/aggregation/disease` | Citeline / Pharmaprojects | Drug programs aggregated by disease |
| `drug/program/aggregation/region` | Citeline / Pharmaprojects | Drug programs aggregated by region |
| `trial` | Citeline / Trialtrove | Clinical trial information |
| `trial/drugtargets` | Citeline / Trialtrove | Drug targets associated to trials |
| `investigator` | Citeline / Sitetrove | Investigator/site profiles |
| `organization` | Citeline / Sitetrove | Clinical research organisation profiles |
| `organization/hierarchy` | Citeline / Sitetrove | Relationships between organisations |
| `organization/trials` | Citeline / Sitetrove | Trials associated to organisations |
| `hcp/profile` | Citeline / Sitetrove | Healthcare Professional (HCP) profiles |
| `physician/profile` | Citeline / Sitetrove | Physician profiles |
| `drugevent` | Biomedtracker (BMT) | Drug events |
| `drugevent/company` | BMT | Drug event company associations |
| `drugevent/profile` | BMT | Drug profile information |
| `drugcatalyst` | BMT | Catalyst information |
| `drugcatalyst/company` | BMT | Catalyst company associations |
| `drugcatalyst/timeseries` | BMT | Historical company-ownership for catalysts |
| `deal` | BMT | Deals for companies and products |
| `device/product` | Meddevicetracker (MDT) | Medical device product profiles |
| `device/trial` | MDT | Device clinical trials |
| `device/event` | MDT | Device events |
| `device/catalyst` | MDT | Device catalysts |
| `device/catalyst/company` | MDT | Device catalyst company associations |
| `device/company` | MDT | Device company associations |
| `patientProximity/investigator` | Patient Proximity | Investigator patient proximity (Sitetrove + SKIPTA) |
| `patientProximity/organization` | Patient Proximity | Organisation patient proximity |
| `patientProximity/Physician` | Patient Proximity | Physician patient proximity (SKIPTA) |
| `patientProximity/hcp` | Patient Proximity | HCP patient proximity (SKIPTA) |
| `patientdiversity/investigator` | Patient Diversity | Investigator patient diversity (Sitetrove + SKIPTA) |
| `patientdiversity/organization` | Patient Diversity | Organisation patient diversity |
| `patientdiversity/physician` | Patient Diversity | Physician patient diversity |
| `patientdiversity/hcp` | Patient Diversity | HCP patient diversity |
| `patientdiversity/global/organization` | Patient Diversity | Global organisation patient diversity |

### Analytics Resources (accessible via `/v1/analytics/{resource}`)

| Resource path | Product | Description |
|---|---|---|
| `analytics/drug` | Citeline Analytics / Pharmaprojects | Drug analytics |
| `analytics/trial` | Citeline Analytics / Trialtrove | Trial analytics |
| `analytics/investigator` | Citeline Analytics / Sitetrove | Investigator analytics |
| `analytics/organization` | Citeline Analytics / Sitetrove | Organisation analytics |

### Insights Resources (accessible via `/v2/search/insights/{publication}`)

Insights APIs cover expert commentary publications. Each publication has a main listing and `/asset` (full-text) sub-resource:

| Publication | Resource path | Description |
|---|---|---|
| Generics Bulletin | `insights/gb` | Generics industry news |
| HBW Insight | `insights/hbw` | Healthcare business news |
| In Vivo | `insights/invivo` | Pharma/Biotech strategic commentary |
| Medtech Insight | `insights/mti` | MedTech news |
| Pink Sheet | `insights/pink` | Pharma regulatory/business news |
| Scrip | `insights/scrip` | Pharma business news |
| Contract Deals | `insights/cd` | Contract deals |

### TrialTrove Plus (accessible via `/v1/trialtrove/plus/{metric}`)

Statistical/analytics endpoints for trial-level metrics. 15 endpoints covering:
`ppspm_by_therapeutic_area`, `ppspm_by_disease`, `ppspm_by_patient_segment`, `ppspm_by_country`, `enrollment_by_quartile`, `site_enrollment_rate`, `sfr_by_therapeutic_area`, `sfr_by_disease`, `sfr_by_patient_segment`, `sfr_by_country`, `recruit_by_country`, `fsa_to_fca_by_month`, `fsa_to_fpa_by_country`, `percentage_cumulative_sites_and_patients`.

### ExpertFinder (accessible via `/v1/sitetrove/plus/expertfinder/{resource}`)

28 endpoints for key opinion leader identification. Core resources: `expertSearch`, `expertDetails`, `expertsStats`, `expertCount`, `trial`, `publication`, `paymentFilter`, `patientPrescribedDrug`, `grantFilter`.

---

## Object Schema

### Schema via API

Every feed and search resource exposes a schema endpoint:

```
GET https://api.citeline.com/v1/feed/{resource}/schema
GET https://api.citeline.com/v1/search/{resource}/schema

Authorization: Bearer <access_token>
Accept: application/json        # returns JSON schema
# OR
Accept: application/xml         # returns XML schema
```

Optional parameter:
- `bareType=true` — returns a minimal type-only schema (no descriptions)

**Example — get trial schema:**
```
GET https://api.citeline.com/v1/feed/trial/schema
Authorization: Bearer <access_token>
```

The schema endpoint returns the full JSON object model describing all fields for that resource. Field descriptions are in the Data Model section of the Citeline developer portal at `https://docs.api.citeline.com/data-model`.

### Static Envelope Schema

All feed responses share a common envelope defined in the OpenAPI spec at `https://api.citeline.com/swagger/v1/swagger.json`:

```json
// FeedPageResponseEnvelope
{
  "meta": {
    "statusCode": 200,
    "message": "OK",
    "version": "v1",
    "schemaVersion": "<version>",
    "generated": "<ISO datetime>",
    "queryUrl": "<url used>",
    "totalRecordCount": 12500
  },
  "pagination": {
    "nextPage": "https://api.citeline.com/v1/feed/trial?forwardToken={token}",
    "previousPage": null
  },
  "items": [
    { "id": 12345, ... }
  ]
}
```

The `items` array contains objects whose fields are resource-specific and defined by the schema endpoint. Each record always has at minimum an `id` field (integer, int64).

---

## Get Object Primary Keys

Primary keys are **static per resource** — every resource uses `id` (integer, int64) as its primary key. This is confirmed by the OpenAPI spec's `BaseEntity` definition and the documented incremental strategy (changes identified by `id`).

| Resource | Primary Key | Type |
|---|---|---|
| All core feed resources | `id` | integer (int64) |

TBD: Verify that all resources expose `id` consistently when schema endpoints are called at runtime — some aggregation sub-resources may use composite keys or lack a single numeric identifier.

---

## Object Ingestion Type

### CDC with Deletes — `/v1/feed/{resource}/changes`

All core feed resources that expose a `/changes` endpoint support **full `cdc_with_deletes`** ingestion. The `/changes?since=YYYY-MM-DD&type=remove` endpoint explicitly returns deleted record IDs.

| Resource | Ingestion Type | Notes |
|---|---|---|
| `drug` | `cdc_with_deletes` | Has `/changes` endpoint |
| `drug/trends` | `cdc_with_deletes` | Has `/changes` endpoint |
| `drug/program` | `cdc_with_deletes` | Has `/changes` endpoint |
| `drug/company` | `cdc_with_deletes` | Has `/changes` endpoint |
| `drug/program/aggregation/*` | `cdc_with_deletes` | All aggregation paths have `/changes` |
| `trial` | `cdc_with_deletes` | Has `/changes` endpoint |
| `trial/drugtargets` | `cdc_with_deletes` | Has `/changes` endpoint |
| `investigator` | `cdc_with_deletes` | Has `/changes` endpoint |
| `organization` | `cdc_with_deletes` | Has `/changes` endpoint |
| `organization/hierarchy` | `cdc_with_deletes` | Has `/changes` endpoint |
| `organization/trials` | `cdc_with_deletes` | Has `/changes` endpoint |
| `hcp/profile` | `cdc_with_deletes` | Has `/changes` endpoint |
| `physician/profile` | `cdc_with_deletes` | Has `/changes` endpoint |
| `drugevent` | `cdc_with_deletes` | Has `/changes` endpoint |
| `drugevent/company` | `cdc_with_deletes` | Has `/changes` endpoint |
| `drugevent/profile` | `cdc_with_deletes` | Has `/changes` endpoint |
| `drugcatalyst` | `cdc_with_deletes` | Has `/changes` endpoint |
| `drugcatalyst/company` | `cdc_with_deletes` | Has `/changes` endpoint |
| `drugcatalyst/timeseries` | `cdc_with_deletes` | Has `/changes` endpoint |
| `deal` | `cdc_with_deletes` | Has `/changes` endpoint |
| `device/product` | `cdc_with_deletes` | Has `/changes` endpoint |
| `device/trial` | `cdc_with_deletes` | Has `/changes` endpoint |
| `device/event` | `cdc_with_deletes` | Has `/changes` endpoint |
| `device/catalyst` | `cdc_with_deletes` | Has `/changes` endpoint |
| `device/catalyst/company` | `cdc_with_deletes` | Has `/changes` endpoint |
| `device/company` | `cdc_with_deletes` | Has `/changes` endpoint |
| `patientProximity/investigator` | `cdc_with_deletes` | Has `/changes` endpoint |
| `patientProximity/organization` | `cdc_with_deletes` | Has `/changes` endpoint |
| `patientProximity/Physician` | `cdc_with_deletes` | Has `/changes` endpoint |
| `patientProximity/hcp` | `cdc_with_deletes` | Has `/changes` endpoint |
| `patientdiversity/investigator` | `cdc_with_deletes` | Has `/changes` endpoint |
| `patientdiversity/organization` | `cdc_with_deletes` | Has `/changes` endpoint |
| `patientdiversity/physician` | `cdc_with_deletes` | Has `/changes` endpoint |
| `patientdiversity/hcp` | `cdc_with_deletes` | Has `/changes` endpoint |
| `patientdiversity/global/organization` | `cdc_with_deletes` | Has `/changes` endpoint |

### Snapshot — Analytics, Insights, Aggregations, TrialTrove Plus, ExpertFinder

These resources do not expose a `/changes` endpoint and must be read as full snapshots:

| Resource | Ingestion Type | Notes |
|---|---|---|
| `analytics/drug` | `snapshot` | No `/changes` endpoint |
| `analytics/trial` | `snapshot` | No `/changes` endpoint |
| `analytics/investigator` | `snapshot` | No `/changes` endpoint |
| `analytics/organization` | `snapshot` | No `/changes` endpoint |
| `v2/search/insights/*` | `snapshot` | Article-based; use `from`/`to` date params for filtering |
| `/v1/trialtrove/plus/*` | `snapshot` | Aggregation/statistical metrics |
| `/v1/sitetrove/plus/expertfinder/*` | `snapshot` | Expert search results |

---

## Read API for Data Retrieval

### Feed Endpoint (Primary Data Ingestion)

**Full feed (initial load):**
```
GET https://api.citeline.com/v1/feed/{resource}
Authorization: Bearer <access_token>
```

Query parameters:

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `forwardToken` | string | No | — | Pagination token from `pagination.nextPage` for the next page |
| `sort` | string | No | `id` | Field to sort by |
| `fields` | string | No | all | Comma-separated list of fields to include in the response |
| `exclude` | boolean | No | `false` | When `true`, `fields` is treated as an exclusion list |
| `pagesize` | integer | No | `100` | Records per page (max: **2,500**) |

**Example — first page of trials:**
```
GET https://api.citeline.com/v1/feed/trial?pagesize=1000
Authorization: Bearer <access_token>
```

**Example — subsequent page using forwardToken:**
```
GET https://api.citeline.com/v1/feed/trial?forwardToken={token_from_nextPage}
Authorization: Bearer <access_token>
```

**Incremental changes feed:**
```
GET https://api.citeline.com/v1/feed/{resource}/changes
Authorization: Bearer <access_token>
```

Query parameters:

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `since` | string | No | — | ISO date string `YYYY-MM-DD` — return changes on or after this date |
| `forwardToken` | string | No | — | Pagination token for the next changes page |
| `sort` | string | No | `id` | Sort field |
| `order` | string | No | `asc` | Sort direction: `asc` or `desc` |
| `fields` | string | No | all | Fields to include |
| `exclude` | boolean | No | `false` | Treat `fields` as exclusion list |
| `type` | string | No | all | Filter change type: `create`, `change`, or `remove` |

**Example — trial changes since 2024-01-01:**
```
GET https://api.citeline.com/v1/feed/trial/changes?since=2024-01-01
Authorization: Bearer <access_token>
```

**Example — deleted trials since 2024-01-01:**
```
GET https://api.citeline.com/v1/feed/trial/changes?since=2024-01-01&type=remove
Authorization: Bearer <access_token>
```

### Changes Response (ChangeItem)

The `/changes` endpoint returns `ChangesResponseEnvelope`, with `items` as an array of `ChangeItem`:

```json
{
  "meta": { "..." },
  "pagination": { "nextPage": "...", "previousPage": null },
  "items": [
    {
      "id": 12345,
      "type": "change",
      "data": { "id": 12345, ...full record... },
      "date": "2024-06-01",
      "note": "Updated status"
    }
  ]
}
```

`ChangeItem` fields:
- `id` (integer) — record ID
- `type` (string) — `"create"`, `"change"`, or `"remove"`
- `data` (object) — full current record (absent for `"remove"` entries)
- `date` (string) — date of change
- `note` (string) — description of what changed

### Record Count Endpoint

```
GET https://api.citeline.com/v1/feed/{resource}/count
Authorization: Bearer <access_token>
```

Returns the total record count. Use to validate completeness of an ingestion run.

### Search Endpoint (Filtered Retrieval)

The search endpoint supports fine-grained filtering. In addition to `GET` with query parameters, many resources also accept a `POST` body with a JSON query expression:

**POST search example — trials updated since 2024-01-01:**
```
POST https://api.citeline.com/v1/search/trial
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "and": [
        {
            "gte": {
                "value": "2024-01-01",
                "name": "updatedDate"
            }
        }
    ]
}
```

Search pagination uses `forwardToken` (cursor-based, sequential page numbers).

### Recommended Incremental Strategy (Three-Step)

The official documentation recommends the following approach for incremental synchronisation:

**Step 1 — Initial / periodic full load (INSERT)**
```python
# GET /v1/feed/{resource}?pagesize=2500 and paginate via forwardToken
# until pagination.nextPage is absent
```

**Step 2 — Identify changed and created records (UPSERT)**
```python
# POST /v1/search/{resource} with updatedDate.gte = last_sync_date
# OR: GET /v1/feed/{resource}/changes?since=last_sync_date&type=change
# OR: GET /v1/feed/{resource}/changes?since=last_sync_date&type=create
```

**Step 3 — Identify deleted records (DELETE)**
```python
# GET /v1/feed/{resource}/changes?since=last_sync_date&type=remove
# Returns records where type="remove" — use the id field to delete from destination
```

### Rate Limits

- HTTP **429 Too Many Requests** is returned when the limit is exceeded (per token, per IP, or per application).
- The response includes a `Retry-After` header indicating when the next request can be made.
- Specific numeric limits (requests/minute or requests/hour) are **TBD** — not published in the documentation; contact Citeline support for current quota values.

### Insights API (v2)

Insights endpoints use different parameters:

```
GET https://api.citeline.com/v2/search/insights/{publication}
?page=1&pagesize=50
Authorization: Bearer <access_token>
```

For removed/deleted articles:
```
GET https://api.citeline.com/v2/search/insights/{publication}?type=remove&from=YYYY-MM-DD&to=YYYY-MM-DD&pageNumber=1&pageSize=100
```

---

## Field Type Mapping

The Citeline API uses JSON field types that map to Spark/connector types as follows:

| API JSON type | Example fields | Spark type | Notes |
|---|---|---|---|
| integer (int32/int64) | `id`, `siteCount`, `trialCount` | `LongType` | Use 64-bit for all integers to avoid overflow; API spec uses `int64` for `id` |
| string | `name`, `status`, `phase`, `country`, `email` | `StringType` | Identifiers and text fields |
| boolean | `active`, `archived` | `BooleanType` | Standard true/false |
| ISO 8601 date | `updatedDate`, `startDate`, `date` | `StringType` | Store as string; format `YYYY-MM-DD`; cast to DATE downstream |
| ISO 8601 datetime | `generated`, `completedTime` | `StringType` | Store as string; cast to TIMESTAMP downstream |
| float/number | `patientsPerSitePerMonth`, `siteEnrollmentRate` | `DoubleType` | Numeric metrics from analytics and TrialTrove Plus |
| object / nested | `trialSponsors`, `trialDiseases`, `trialTherapeuticAreas`, `primaryEndpoints` | `StringType` (JSON) | Complex nested objects should be serialised to JSON strings; parse with `from_json()` downstream |
| array of objects | `trialDrugs`, `trialSites`, `investigators` | `StringType` (JSON) | Arrays of objects serialised as JSON strings |

> **Note**: Field schemas vary per resource and are not enumerated in the main OpenAPI spec (the `items` type is `BaseEntity` with only `id`). The actual field list for each resource is available via `GET /v1/feed/{resource}/schema`. Schemas should be fetched at connector init time to determine field-level types.

---

## Sources and References

## Research Log

| Source Type | URL | Accessed (UTC) | Confidence | What it confirmed |
|---|---|---|---|---|
| Official Docs SPA | https://docs.api.citeline.com/ | 2026-06-04 | High | Auth flow, endpoint patterns, resources table, pagination, rate limits, incremental strategy |
| Official OpenAPI Spec (main) | https://api.citeline.com/swagger/v1/swagger.json | 2026-06-04 | Highest | 678 paths, all feed/search endpoints, security definition (Bearer), response envelope schemas, ChangeItem schema, parameter names |
| Official OpenAPI Spec (TrialTrove Plus) | https://api.citeline.com/swagger/v1/swagger-trialTrove-plus.json | 2026-06-04 | Highest | 15 TrialTrove Plus metric endpoints |
| Official OpenAPI Spec (ExpertFinder) | https://api.citeline.com/swagger/v1/swagger-expertFinder.json | 2026-06-04 | Highest | 28 ExpertFinder endpoints |
| Main JS Bundle | https://docs.api.citeline.com/static/js/main.9612c13a.js | 2026-06-04 | High | Resources table with descriptions, auth code examples, pagination documentation (default 100, max 2500), since date format, 3-step incremental strategy, Retry-After rate limit header |

No existing Airbyte, Singer, or dltHub Citeline connector was found during research. All documentation derived from official Citeline sources.

### Known Quirks and TBDs

- **TBD: Rate limit numbers** — The documentation confirms 429 + Retry-After behaviour but does not publish specific quota values. Contact Citeline support or test empirically.
- **TBD: `since` date granularity** — The docs show `YYYY-MM-DD` format. Sub-day precision (datetime) may not be supported for the `since` parameter; use date-only strings.
- **TBD: `pagesize` on `/changes`** — The `pagesize` parameter is documented for the feed endpoint. Whether it applies to `/changes` endpoints needs runtime verification.
- **TBD: Aggregation resource primary keys** — `drug/program/aggregation/*` resources may use composite keys rather than a single `id`. Verify with schema endpoint.
- **TBD: Insights v2 incremental cursor** — The `/v2/search/insights/{publication}` endpoint uses `from`/`to` date parameters. No `changes` endpoint exists; full snapshot or date-windowed incremental is the recommended approach.
- **Authentication note** — The Swagger `SSOTokenRequest` schema requires `username`, `email`, and `password`. The official documentation only shows `email` + `password`. Prefer `email` + `password` only, as shown in the Python example in official docs. The `username` field may be deprecated or identical to email.
- **Token validity** — `expires_in: 86400` (24 hours). The connector should fetch a new token at the start of each ingestion run or implement a refresh strategy.

---

## Live Validation Notes

*Validated against account `nenad.milic@worldwide.com` on 2026-06-04.*

### Account Access Scope

This account has a **Trialtrove + Sitetrove** subscription. Only 6 of 33 feed endpoints return 200; all others return 403:

| Endpoint | Status | Fields |
|---|---|---|
| `/v1/feed/trial` | ✅ 200 | 54 |
| `/v1/feed/trial/drugtargets` | ✅ 200 | 5 |
| `/v1/feed/investigator` | ✅ 200 | 32 |
| `/v1/feed/organization` | ✅ 200 | 33 |
| `/v1/feed/organization/hierarchy` | ✅ 200 | 8 |
| `/v1/feed/organization/trials` | ✅ 200 | 10 |
| All other feed endpoints | ❌ 403 | — |

> **Implication for the connector**: Feed access is subscription-gated at the API level with 403. The connector's `list_tables` should only expose endpoints the account can actually access, or handle 403 gracefully with a clear error message.

### Primary Key Corrections (live data, overrides spec assumptions)

The `id` field from `BaseEntity` in the OpenAPI spec is **not present** on actual response records. Each resource uses its own named ID field:

| Resource | Actual Primary Key | Type | Notes |
|---|---|---|---|
| `trial` | `trialId` | integer | Not `id` |
| `trial/drugtargets` | `trialId` | integer | Composite with drug target fields |
| `investigator` | `investigatorId` | integer | |
| `organization` | `organizationId` | integer | |
| `organization/hierarchy` | `organizationId` | integer | No per-relationship unique key |
| `organization/trials` | `organizationTrialId` | integer | Bridge table; also carries `organizationId` + `trialId` |

### Incremental Cursor Field

All accessible resources include `updatedDate` (ISO 8601 datetime string, UTC, e.g. `2026-06-04T03:31:52.065Z`). This is the correct cursor field for CDC incremental reads — not `since` on the feed endpoint, but as a POST search filter on `/v1/search/{resource}` with `updatedDate.gte`.

### `$type` Field

Every record contains a `$type` field (e.g. `Pharma.Api.Schema.Trial.Trial, Pharma.Api.Schema`) identifying the .NET class. This should be treated as a string metadata field, not a primary key.

### `totalRecordCount` in Meta

The `meta.totalRecordCount` field is **not populated** on the main feed endpoint (`/v1/feed/trial` returns `null`). Use `/v1/feed/{resource}/count` instead for total counts. It **is** populated on `/v1/feed/{resource}/changes` responses (verified: 12,199 removed trials since 2025-06-01).
