# Lakeflow Citeline Community Connector

This documentation provides setup instructions and reference information for the Citeline source connector. The Citeline connector ingests pharma, clinical-trials, and life-sciences data from the Informa Citeline V1 Feed API (`https://api.citeline.com`), covering Pharmaprojects, Trialtrove, Sitetrove, Biomedtracker (BMT), Meddevicetracker (MDT), Patient Proximity, and Patient Diversity products.

## Prerequisites

- A registered Citeline (Informa) account with API access enabled.
- Email and password credentials for the account.
- Your Citeline subscription determines which feed endpoints are accessible. The connector gracefully handles 403/404 responses for resources not included in your subscription.

## Setup

### Required Connection Parameters

To configure the connector, provide the following parameters in your connector options:

| Parameter | Type | Required | Description | Example |
|---|---|---|---|---|
| `email` | String | Yes | Email address registered with your Citeline account. Submitted to `POST https://api.citeline.com/token` to obtain a Bearer token. | `user@company.com` |
| `password` | String (secret) | Yes | Password associated with your Citeline account email. Combined with email to obtain a short-lived JWT Bearer token (valid 24 hours). | `MySecurePassw0rd!` |

This connector supports one table-specific option that must be included in the `externalOptionsAllowList` parameter of the UC connection:

| Parameter | Type | Required | Description | Example |
|---|---|---|---|---|
| `externalOptionsAllowList` | String | Yes | Comma-separated list of table-specific options to pass through. Must be set to: `max_records_per_batch` | `max_records_per_batch` |

### Obtaining Credentials

1. Register for a Citeline account at [https://www.citeline.com](https://www.citeline.com) or through your organization's Informa representative.
2. Ensure your subscription includes API access to the desired product lines (Pharmaprojects, Trialtrove, Sitetrove, BMT, MDT, etc.).
3. Use the email and password from your Citeline account registration as the connection parameters.

The connector authenticates by exchanging `email` + `password` for a short-lived JWT Bearer token via `POST https://api.citeline.com/token`. Tokens expire in 24 hours (`expires_in: 86400`). A fresh token is obtained on every connector initialization — no manual token management is required.

### Create a Unity Catalog Connection

A Unity Catalog connection for this connector can be created in two ways via the UI:
1. Follow the Lakeflow Community Connector UI flow from the "Add Data" page.
2. Select any existing Lakeflow Community Connector connection for Citeline or create a new one.
3. Set `externalOptionsAllowList` to `max_records_per_batch` to enable per-table configuration of page sizes.

The connection can also be created using the standard Unity Catalog API.


## Supported Objects

The connector exposes a static list of 38 feed resources across six product lines. All objects are accessed under `https://api.citeline.com/v1/feed/{resource}` and use **CDC with deletes** ingestion mode with `updatedDate` as the cursor field.

Delete synchronization is supported for all objects via the `/v1/feed/{resource}/changes?type=remove` endpoint, which returns tombstone records containing the primary key and `updatedDate` fields.

### Pharmaprojects

| Object | Primary Key | Ingestion Mode | Cursor Field | Delete Sync |
|---|---|---|---|---|
| `drug` | `id` | CDC with deletes | `updatedDate` | Yes |
| `drug_trends` | `id` | CDC with deletes | `updatedDate` | Yes |
| `drug_program` | `id` | CDC with deletes | `updatedDate` | Yes |
| `drug_company` | `id` | CDC with deletes | `updatedDate` | Yes |
| `drug_program_agg_company` | `id` | CDC with deletes | `updatedDate` | Yes |
| `drug_program_agg_country` | `id` | CDC with deletes | `updatedDate` | Yes |
| `drug_program_agg_disease` | `id` | CDC with deletes | `updatedDate` | Yes |
| `drug_program_agg_region` | `id` | CDC with deletes | `updatedDate` | Yes |

### Trialtrove

| Object | Primary Key | Ingestion Mode | Cursor Field | Delete Sync |
|---|---|---|---|---|
| `trial` | `trialId` | CDC with deletes | `updatedDate` | Yes |
| `trial_drugtargets` | `trialId` | CDC with deletes | `updatedDate` | Yes |

### Sitetrove

| Object | Primary Key | Ingestion Mode | Cursor Field | Delete Sync |
|---|---|---|---|---|
| `investigator` | `investigatorId` | CDC with deletes | `updatedDate` | Yes |
| `organization` | `organizationId` | CDC with deletes | `updatedDate` | Yes |
| `organization_hierarchy` | `organizationId` | CDC with deletes | `updatedDate` | Yes |
| `organization_trials` | `organizationTrialId` | CDC with deletes | `updatedDate` | Yes |
| `hcp_profile` | `id` | CDC with deletes | `updatedDate` | Yes |
| `physician_profile` | `id` | CDC with deletes | `updatedDate` | Yes |

### Biomedtracker (BMT)

| Object | Primary Key | Ingestion Mode | Cursor Field | Delete Sync |
|---|---|---|---|---|
| `drugevent` | `id` | CDC with deletes | `updatedDate` | Yes |
| `drugevent_company` | `id` | CDC with deletes | `updatedDate` | Yes |
| `drugevent_profile` | `id` | CDC with deletes | `updatedDate` | Yes |
| `drugcatalyst` | `id` | CDC with deletes | `updatedDate` | Yes |
| `drugcatalyst_company` | `id` | CDC with deletes | `updatedDate` | Yes |
| `drugcatalyst_timeseries` | `id` | CDC with deletes | `updatedDate` | Yes |
| `deal` | `id` | CDC with deletes | `updatedDate` | Yes |

### Meddevicetracker (MDT)

| Object | Primary Key | Ingestion Mode | Cursor Field | Delete Sync |
|---|---|---|---|---|
| `device_product` | `id` | CDC with deletes | `updatedDate` | Yes |
| `device_trial` | `id` | CDC with deletes | `updatedDate` | Yes |
| `device_event` | `id` | CDC with deletes | `updatedDate` | Yes |
| `device_catalyst` | `id` | CDC with deletes | `updatedDate` | Yes |
| `device_catalyst_company` | `id` | CDC with deletes | `updatedDate` | Yes |
| `device_company` | `id` | CDC with deletes | `updatedDate` | Yes |

### Patient Proximity & Diversity

| Object | Primary Key | Ingestion Mode | Cursor Field | Delete Sync |
|---|---|---|---|---|
| `patientproximity_investigator` | `id` | CDC with deletes | `updatedDate` | Yes |
| `patientproximity_organization` | `id` | CDC with deletes | `updatedDate` | Yes |
| `patientproximity_physician` | `id` | CDC with deletes | `updatedDate` | Yes |
| `patientproximity_hcp` | `id` | CDC with deletes | `updatedDate` | Yes |
| `patientdiversity_investigator` | `id` | CDC with deletes | `updatedDate` | Yes |
| `patientdiversity_organization` | `id` | CDC with deletes | `updatedDate` | Yes |
| `patientdiversity_physician` | `id` | CDC with deletes | `updatedDate` | Yes |
| `patientdiversity_hcp` | `id` | CDC with deletes | `updatedDate` | Yes |
| `patientdiversity_global_organization` | `id` | CDC with deletes | `updatedDate` | Yes |

### Ingestion Strategy

- **First run (full feed)**: The connector paginates through the entire feed via `/v1/feed/{resource}` using `forwardToken`-based pagination until all records are consumed.
- **Subsequent runs (incremental)**: The connector calls `/v1/feed/{resource}/changes?since={cursor}` to fetch only `create` and `change` items since the last cursor position.
- **Delete synchronization**: Separately calls `/v1/feed/{resource}/changes?type=remove` to retrieve tombstone records containing the primary key field and `updatedDate`.
- **Lookback safety**: A 1-day lookback is subtracted from the cursor on the first incremental call per trigger to handle late-arriving changes and ensure no records are missed.

## Table Configurations

### Source & Destination

These are set directly under each `table` object in the pipeline spec:

| Option | Required | Description |
|---|---|---|
| `source_table` | Yes | Table name in the source system (one of the 38 supported objects listed above) |
| `destination_catalog` | No | Target catalog (defaults to pipeline's default) |
| `destination_schema` | No | Target schema (defaults to pipeline's default) |
| `destination_table` | No | Target table name (defaults to `source_table`) |

### Common `table_configuration` options

These are set inside the `table_configuration` map alongside any source-specific options:

| Option | Required | Description |
|---|---|---|
| `scd_type` | No | `SCD_TYPE_1` (default) or `SCD_TYPE_2`. Applies to all tables since all use CDC ingestion mode. |
| `primary_keys` | No | List of columns to override the connector's default primary keys |
| `sequence_by` | No | Column used to order records for SCD Type 2 change tracking |

### Special `table_configuration` options

| Option | Applicable Objects | Required | Description | Default |
|---|---|---|---|---|
| `max_records_per_batch` | All objects | No | Maximum number of records to fetch per API page. Controls the `pagesize` parameter sent to the Citeline API. Capped at 2500 (the API maximum). | `200` |


## Data Type Mapping

Schemas are fetched dynamically from the `/v1/feed/{resource}/schema` endpoint at runtime. The API returns a JSON Schema envelope; the connector extracts the item-level schema and maps types as follows:

| JSON Schema Type | Spark SQL Type | Notes |
|---|---|---|
| `string` | `StringType` | Includes dates returned as ISO strings |
| `integer` | `LongType` | All integers mapped to 64-bit |
| `number` | `DoubleType` | Floating-point numbers |
| `boolean` | `BooleanType` | |
| `object` | `StringType` | Nested objects serialized as JSON strings |
| `array` | `StringType` | Arrays serialized as JSON strings |
| `$ref` | Resolved recursively | JSON Schema references are followed to their definitions |
| `anyOf`/`oneOf` | First non-null type | Union types resolved to the first concrete candidate |

When the schema endpoint returns 403 (not in subscription) or 404, a minimal fallback schema is used containing only the primary key field(s) and `updatedDate`.


## How to Run

### Step 1: Clone/Copy the Source Connector Code
Follow the Lakeflow Community Connector UI, which will guide you through setting up a pipeline using the selected source connector code.

### Step 2: Configure Your Pipeline
1. Update the `pipeline_spec` in the main pipeline file (e.g., `ingest.py`).
2. Configure each object with the appropriate table-specific options:

```json
{
  "pipeline_spec": {
      "connection_name": "my_citeline_connection",
      "object": [
        {
            "table": {
                "source_table": "trial",
                "table_configuration": {
                    "max_records_per_batch": "500"
                }
            }
        },
        {
            "table": {
                "source_table": "drug",
                "table_configuration": {
                    "max_records_per_batch": "500"
                }
            }
        },
        {
            "table": {
                "source_table": "investigator",
                "table_configuration": {
                    "max_records_per_batch": "1000"
                }
            }
        },
        {
            "table": {
                "source_table": "organization",
                "table_configuration": {
                    "max_records_per_batch": "1000"
                }
            }
        },
        {
            "table": {
                "source_table": "device_product",
                "table_configuration": {
                    "max_records_per_batch": "500"
                }
            }
        }
      ]
  }
}
```
3. (Optional) Customize the source connector code if needed for special use cases.

### Step 3: Run and Schedule the Pipeline

#### Best Practices

- **Start Small**: Begin by syncing a subset of objects to verify your Citeline subscription covers them.
- **Use Incremental Sync**: The connector automatically uses incremental CDC after the first full load — no configuration needed.
- **Monitor 403 Responses**: Tables returning HTTP 403 are not included in your subscription; the connector returns empty results gracefully without failing the pipeline.
- **Page Size Tuning**: Increase `max_records_per_batch` (up to 2500) for large tables to reduce the total number of API calls.
- **Set Appropriate Schedules**: The Citeline API rate-limits requests; avoid running the pipeline more frequently than every few hours for large table sets.
- **Token Expiry**: Tokens are valid for 24 hours. For long-running initial loads, the connector fetches a single token at startup — ensure your pipeline completes within that window or configure smaller batches.

#### Troubleshooting

**Common Issues:**

| Issue | Resolution |
|---|---|
| 401 Unauthorized | Verify email and password are correct. Ensure the account has API access enabled. |
| 403 Forbidden on specific tables | The table/resource is not included in your Citeline subscription. Contact your Informa representative to add it. |
| 429 Too Many Requests | The connector retries automatically with exponential backoff (up to 4 retries). If persistent, reduce `max_records_per_batch` or increase the pipeline schedule interval. |
| 500/502/503/504 Server Errors | Transient API issues — the connector retries automatically. Check Citeline API status if persistent. |
| Empty results after initial load | Verify the `updatedDate` cursor is advancing in subsequent runs. Check that the table is accessible (not returning 403). |
| Schema returns minimal fields only | The schema endpoint returned 403/404 for that resource. A fallback schema with primary key + `updatedDate` is used. Full schema will be available once the subscription is activated. |


## References

- [Citeline API Developer Portal](https://docs.api.citeline.com)
- [Citeline API Base URL](https://api.citeline.com)
- [Citeline Data Model Documentation](https://docs.api.citeline.com/data-model)
- [Informa Pharma Intelligence](https://www.citeline.com)
