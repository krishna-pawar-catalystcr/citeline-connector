"""Citeline (Informa) Lakeflow community connector.

Ingests pharma, clinical-trials, and life-sciences data from the Citeline V1
Feed API (https://api.citeline.com). Covers Pharmaprojects, Trialtrove,
Sitetrove, Biomedtracker (BMT), Meddevicetracker (MDT), and related products.

Authentication: email + password are exchanged for a short-lived JWT Bearer
token via POST /token (expires in 24 hours). The connector fetches a fresh
token on every __init__ call.

All feed resources expose a /changes endpoint and are ingested as
``cdc_with_deletes``:
  - read_table  : full feed on first run, then /changes (create+change) on
                  subsequent runs.
  - read_table_deletes : /changes?type=remove for delete synchronisation.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, date, timedelta, timezone
from typing import Iterator
from urllib.parse import urlparse, parse_qs, urlencode
import urllib.request
import urllib.error

from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
)

from databricks.labs.community_connector.interface import LakeflowConnect


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_BASE_URL = "https://api.citeline.com"
_TOKEN_URL = f"{_BASE_URL}/token"
_MAX_RETRIES = 4
_INITIAL_BACKOFF = 1.0
_RETRIABLE_CODES = {429, 500, 502, 503, 504}
_LOOKBACK_DAYS = 1
_DEFAULT_PAGESIZE = 500
_MAX_PAGESIZE = 2500
# Default 'since' when no cursor is available (avoids HTTP 400 on /changes).
_DEFAULT_SINCE = "2000-01-01"
# Default 'since' when no cursor is available (avoids HTTP 400 on /changes).
_DEFAULT_SINCE = "2000-01-01"


# ---------------------------------------------------------------------------
# Static table catalogue: connector table_name → API resource path
# All resources sit under /v1/feed/{resource} and expose /changes.
# ---------------------------------------------------------------------------
_FEED_TABLES: dict[str, str] = {
    "trial": "trial",
    "trial_drugtargets": "trial/drugtargets",
    "drug": "drug",
    "drug_trends": "drug/trends",
    "drug_program": "drug/program",
    "drug_company": "drug/company",
    "drug_program_agg_company": "drug/program/aggregation/company",
    "drug_program_agg_country": "drug/program/aggregation/country",
    "drug_program_agg_disease": "drug/program/aggregation/disease",
    "drug_program_agg_region": "drug/program/aggregation/region",
    "investigator": "investigator",
    "organization": "organization",
    "organization_hierarchy": "organization/hierarchy",
    "organization_trials": "organization/trials",
    "hcp_profile": "hcp/profile",
    "physician_profile": "physician/profile",
    "drugevent": "drugevent",
    "drugevent_company": "drugevent/company",
    "drugevent_profile": "drugevent/profile",
    "drugcatalyst": "drugcatalyst",
    "drugcatalyst_company": "drugcatalyst/company",
    "drugcatalyst_timeseries": "drugcatalyst/timeseries",
    "deal": "deal",
    "device_product": "device/product",
    "device_trial": "device/trial",
    "device_event": "device/event",
    "device_catalyst": "device/catalyst",
    "device_catalyst_company": "device/catalyst/company",
    "device_company": "device/company",
    "patientproximity_investigator": "patientProximity/investigator",
    "patientproximity_organization": "patientProximity/organization",
    "patientproximity_physician": "patientProximity/Physician",
    "patientproximity_hcp": "patientProximity/hcp",
    "patientdiversity_investigator": "patientdiversity/investigator",
    "patientdiversity_organization": "patientdiversity/organization",
    "patientdiversity_physician": "patientdiversity/physician",
    "patientdiversity_hcp": "patientdiversity/hcp",
    "patientdiversity_global_organization": "patientdiversity/global/organization",
}


# Primary key fields per table, verified from live API data.
# Fallback "id" is used for tables not yet accessible under the test account.
_PRIMARY_KEYS: dict[str, list[str]] = {
    "trial": ["trialId"],
    "trial_drugtargets": ["trialId"],
    "investigator": ["investigatorId"],
    "organization": ["organizationId"],
    "organization_hierarchy": ["organizationId"],
    "organization_trials": ["organizationTrialId"],
}
_DEFAULT_PK = ["id"]

# Maps table_name → the record field populated from ChangeItem.id in delete tombstones.
_PK_FROM_CHANGE_ID: dict[str, str] = {
    "trial": "trialId",
    "trial_drugtargets": "trialId",
    "investigator": "investigatorId",
    "organization": "organizationId",
    "organization_hierarchy": "organizationId",
    "organization_trials": "organizationTrialId",
}
_DEFAULT_PK_CHANGE_FIELD = "id"


# ---------------------------------------------------------------------------
# JSON Schema → Spark type helpers
# ---------------------------------------------------------------------------

def _resolve_ref(ref: str, definitions: dict) -> dict:
    """Resolve a JSON Schema $ref like '#/definitions/Foo' to its definition."""
    if ref.startswith("#/definitions/"):
        name = ref[len("#/definitions/"):]
        return definitions.get(name, {})
    return {}


def _json_schema_to_spark(field_schema: dict, definitions: dict, depth: int = 0):
    """Recursively convert a JSON Schema field definition to a Spark DataType.

    Objects and arrays are mapped to StringType; callers are expected to
    serialize those fields to JSON strings before returning records.
    """
    if depth > 6:
        return StringType()

    if "$ref" in field_schema:
        resolved = _resolve_ref(field_schema["$ref"], definitions)
        return _json_schema_to_spark(resolved, definitions, depth + 1)

    ftype = field_schema.get("type", "")

    # Handle nullable union like ["string", "null"]
    if isinstance(ftype, list):
        non_null = [t for t in ftype if t != "null"]
        ftype = non_null[0] if non_null else "string"

    if ftype == "integer":
        return LongType()
    if ftype == "number":
        return DoubleType()
    if ftype == "boolean":
        return BooleanType()
    if ftype in ("object", "array"):
        return StringType()  # serialised to JSON string
    if ftype == "string":
        return StringType()

    # anyOf / oneOf: take first non-null candidate
    for combiner in ("anyOf", "oneOf"):
        candidates = [
            s for s in field_schema.get(combiner, []) if s.get("type") != "null"
        ]
        if candidates:
            return _json_schema_to_spark(candidates[0], definitions, depth + 1)

    return StringType()


def _parse_item_schema(raw_schema: dict) -> StructType:
    """Extract the item-level Spark StructType from a feed envelope JSON Schema.

    The API returns an envelope schema whose ``items`` array property references
    the actual record definition in ``definitions``.  This function navigates
    that reference and builds a flat StructType.
    """
    definitions = raw_schema.get("definitions", {})

    # Envelope: properties.items (array) → .items.$ref → record definition
    items_array = raw_schema.get("properties", {}).get("items", {})
    item_ref = items_array.get("items", {}).get("$ref", "")

    if item_ref:
        item_def = _resolve_ref(item_ref, definitions)
    else:
        # Fallback: treat the root schema as the item schema
        item_def = raw_schema

    properties = item_def.get("properties", {})
    if not properties:
        return StructType([StructField("data", StringType(), True)])

    return StructType([
        StructField(fname, _json_schema_to_spark(fschema, definitions), True)
        for fname, fschema in properties.items()
    ])


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _extract_forward_token(next_page_url: str | None) -> str | None:
    """Extract the forwardToken query-string value from a nextPage URL."""
    if not next_page_url:
        return None
    try:
        qs = parse_qs(urlparse(next_page_url).query)
        tokens = qs.get("forwardToken", [])
        return tokens[0] if tokens else None
    except Exception:
        return None


def _serialize_record(record: dict) -> dict:
    """Serialize dict/list field values to JSON strings for Spark StringType cols."""
    result = {}
    for k, v in record.items():
        if isinstance(v, (dict, list)):
            result[k] = json.dumps(v, separators=(",", ":"))
        else:
            result[k] = v
    return result


def _apply_lookback(cursor: str) -> str:
    """Subtract _LOOKBACK_DAYS from a YYYY-MM-DD cursor string."""
    try:
        return (date.fromisoformat(cursor) - timedelta(days=_LOOKBACK_DAYS)).isoformat()
    except ValueError:
        return cursor


# ---------------------------------------------------------------------------
# Connector class
# ---------------------------------------------------------------------------

class CitelineLakeflowConnect(LakeflowConnect):
    """LakeflowConnect implementation for the Citeline (Informa) pharma data API."""

    def __init__(self, options: dict[str, str]) -> None:
        super().__init__(options)
        self._token = self._fetch_token(options["email"], options["password"])
        # Cap incremental reads at init time so a trigger never chases live writes.
        self._init_ts: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # Track which tables have already had the lookback subtraction applied
        # during this trigger instance (one connector instance per trigger).
        self._lookback_applied: set[str] = set()
        self._deletes_lookback_applied: set[str] = set()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def _fetch_token(self, email: str, password: str) -> str:
        """POST email+password to /token and return 'Bearer <jwt>'."""
        body = json.dumps({"email": email, "password": password}).encode()
        req = urllib.request.Request(
            _TOKEN_URL,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        return f"Bearer {data['access_token']}"

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _get(self, path: str, params: dict | None = None) -> dict:
        """Authenticated GET with exponential-backoff retry on transient errors.

        Raises urllib.error.HTTPError directly for client errors (4xx) — callers
        may catch 403/404 to handle subscription-gated endpoints gracefully.
        """
        url = f"{_BASE_URL}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"

        backoff = _INITIAL_BACKOFF
        last_err: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            req = urllib.request.Request(
                url, headers={"Authorization": self._token}
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as exc:
                last_err = exc
                # 4xx are client errors — do not retry; let callers handle them.
                if exc.code < 500 or attempt == _MAX_RETRIES - 1:
                    raise
                retry_after = float(
                    exc.headers.get("Retry-After") or backoff
                )
                time.sleep(retry_after)
                backoff = min(backoff * 2, 60.0)
            except urllib.error.URLError as exc:
                last_err = exc
                if attempt == _MAX_RETRIES - 1:
                    raise
                time.sleep(backoff)
                backoff = min(backoff * 2, 60.0)

        raise RuntimeError(
            f"All {_MAX_RETRIES} attempts failed for GET {path}: {last_err}"
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_table(self, table_name: str) -> None:
        if table_name not in _FEED_TABLES:
            raise ValueError(
                f"Table '{table_name}' is not supported. "
                f"Supported tables: {sorted(_FEED_TABLES)}"
            )

    # ------------------------------------------------------------------
    # LakeflowConnect interface
    # ------------------------------------------------------------------

    def list_tables(self) -> list[str]:
        """Return the static list of all 39 Citeline feed resources."""
        return list(_FEED_TABLES.keys())

    def get_table_schema(
        self, table_name: str, table_options: dict[str, str]
    ) -> StructType:
        """Fetch the JSON Schema from /v1/feed/{resource}/schema and convert to StructType.

        The API returns an envelope schema; this method navigates into the
        items definition to produce the per-record Spark schema.  Object and
        array fields are mapped to StringType (JSON strings).

        Returns a minimal fallback schema (primary-key + updatedDate) when the
        endpoint returns 403 (not in subscription) or 404 (not found).
        """
        self._validate_table(table_name)
        resource = _FEED_TABLES[table_name]
        try:
            raw_schema = self._get(f"/v1/feed/{resource}/schema")
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 404):
                # Endpoint not accessible under this subscription — return a
                # minimal schema so the framework can continue.
                pk_fields = _PRIMARY_KEYS.get(table_name, _DEFAULT_PK)
                fields = [StructField(pk, LongType(), True) for pk in pk_fields]
                fields.append(StructField("updatedDate", StringType(), True))
                return StructType(fields)
            raise

        schema = _parse_item_schema(raw_schema)

        # Ensure primary key field(s) and the CDC cursor field are present.
        pk_fields = _PRIMARY_KEYS.get(table_name, _DEFAULT_PK)
        existing = {f.name for f in schema.fields}
        extra: list[StructField] = []
        for pk in pk_fields:
            if pk not in existing:
                extra.append(StructField(pk, LongType(), True))
        if "updatedDate" not in existing:
            extra.append(StructField("updatedDate", StringType(), True))

        return StructType(schema.fields + extra) if extra else schema

    def read_table_metadata(
        self, table_name: str, table_options: dict[str, str]
    ) -> dict:
        """Return static metadata. All Citeline feed resources are cdc_with_deletes."""
        self._validate_table(table_name)
        return {
            "primary_keys": _PRIMARY_KEYS.get(table_name, _DEFAULT_PK),
            "cursor_field": "updatedDate",
            "ingestion_type": "cdc_with_deletes",
        }

    def read_table(
        self,
        table_name: str,
        start_offset: dict,
        table_options: dict[str, str],
    ) -> tuple[Iterator[dict], dict]:
        """Read one microbatch of records.

        Routing logic:
          - start_offset is None OR phase=="feed" → paginate the full feed
            (/v1/feed/{resource}).  Once exhausted, transitions to the
            "changes" phase with cursor = _init_ts.
          - phase=="changes" → paginate /v1/feed/{resource}/changes, extracting
            "create" and "change" items.  "remove" items are skipped (handled
            by read_table_deletes).
          - cursor >= _init_ts → already caught up, returns empty + same offset.
        """
        self._validate_table(table_name)
        resource = _FEED_TABLES[table_name]
        max_records = int(table_options.get("max_records_per_batch", "200"))
        pagesize = min(max_records, _MAX_PAGESIZE)

        # ---- Full-feed phase ----
        if start_offset is None or start_offset.get("phase") == "feed":
            params: dict[str, str] = {"pagesize": str(pagesize)}
            fwd = (start_offset or {}).get("forward_token")
            if fwd:
                params["forwardToken"] = fwd

            try:
                body = self._get(f"/v1/feed/{resource}", params=params)
            except urllib.error.HTTPError as exc:
                if exc.code in (403, 404):
                    # Endpoint not in subscription — return empty + stable offset.
                    return iter([]), {"phase": "changes", "cursor": self._init_ts}
                raise

            records = [_serialize_record(item) for item in body.get("items", [])]

            next_token = _extract_forward_token(
                body.get("pagination", {}).get("nextPage")
            )
            if next_token:
                end_offset: dict = {"phase": "feed", "forward_token": next_token}
            else:
                # Full feed exhausted — switch to incremental changes phase.
                end_offset = {"phase": "changes", "cursor": self._init_ts}

            return iter(records), end_offset

        # ---- Changes phase ----
        cursor = start_offset.get("cursor")

        # Short-circuit: already at or past init time.
        if cursor and cursor >= self._init_ts:
            return iter([]), start_offset

        params = {"pagesize": str(pagesize)}
        fwd = start_offset.get("forward_token")
        if fwd:
            params["forwardToken"] = fwd
        else:
            # Always provide 'since' to avoid HTTP 400 on the changes endpoint.
            effective_since = cursor or _DEFAULT_SINCE
            if cursor and table_name not in self._lookback_applied:
                effective_since = _apply_lookback(cursor)
                self._lookback_applied.add(table_name)
            params["since"] = effective_since

        try:
            body = self._get(f"/v1/feed/{resource}/changes", params=params)
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 404):
                return iter([]), start_offset
            raise

        items = body.get("items", [])

        records = []
        max_date = cursor or ""
        for item in items:
            if item.get("type") == "remove":
                continue  # deletes handled by read_table_deletes
            data = item.get("data")
            if data:
                records.append(_serialize_record(data))
            d = item.get("date", "")
            if d > max_date:
                max_date = d

        next_token = _extract_forward_token(
            body.get("pagination", {}).get("nextPage")
        )
        if next_token:
            end_offset = {
                "phase": "changes",
                "cursor": max_date or cursor,
                "forward_token": next_token,
            }
        else:
            new_cursor = max_date if max_date else (cursor or self._init_ts)
            end_offset = {"phase": "changes", "cursor": new_cursor}

        # If nothing changed (cursor didn't advance, no records), signal done.
        if not records and end_offset == start_offset:
            return iter([]), start_offset

        return iter(records), end_offset

    def read_table_deletes(
        self,
        table_name: str,
        start_offset: dict,
        table_options: dict[str, str],
    ) -> tuple[Iterator[dict], dict]:
        """Read one microbatch of delete tombstones from /v1/feed/{resource}/changes?type=remove.

        Returns records containing only the primary key field and updatedDate
        (populated from ChangeItem.id and ChangeItem.date respectively).
        """
        self._validate_table(table_name)
        resource = _FEED_TABLES[table_name]
        max_records = int(table_options.get("max_records_per_batch", "200"))
        pagesize = min(max_records, _MAX_PAGESIZE)

        cursor = (start_offset or {}).get("cursor")
        if cursor and cursor >= self._init_ts:
            return iter([]), start_offset

        params: dict[str, str] = {"type": "remove", "pagesize": str(pagesize)}
        fwd = (start_offset or {}).get("forward_token")
        if fwd:
            params["forwardToken"] = fwd
        else:
            # Always provide 'since' to avoid HTTP 400 on the changes endpoint.
            effective_since = cursor or _DEFAULT_SINCE
            if cursor and table_name not in self._deletes_lookback_applied:
                effective_since = _apply_lookback(cursor)
                self._deletes_lookback_applied.add(table_name)
            params["since"] = effective_since

        try:
            body = self._get(f"/v1/feed/{resource}/changes", params=params)
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 404):
                return iter([]), start_offset or {"cursor": self._init_ts}
            raise
        items = body.get("items", [])

        pk_field = _PK_FROM_CHANGE_ID.get(table_name, _DEFAULT_PK_CHANGE_FIELD)
        records: list[dict] = []
        max_date = cursor or ""
        for item in items:
            change_id = item.get("id")
            date_str = item.get("date", "")
            records.append({pk_field: change_id, "updatedDate": date_str})
            if date_str > max_date:
                max_date = date_str

        next_token = _extract_forward_token(
            body.get("pagination", {}).get("nextPage")
        )
        if next_token:
            end_offset: dict = {
                "cursor": max_date or cursor,
                "forward_token": next_token,
            }
        else:
            new_cursor = max_date if max_date else (cursor or self._init_ts)
            end_offset = {"cursor": new_cursor}

        # No records and cursor didn't advance — signal done.
        if not records and not next_token:
            stable_offset = start_offset or {"cursor": self._init_ts}
            if end_offset == stable_offset or start_offset is None:
                return iter([]), end_offset

        if start_offset and end_offset == start_offset:
            return iter([]), start_offset

        return iter(records), end_offset
