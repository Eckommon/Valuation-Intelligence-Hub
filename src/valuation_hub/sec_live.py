"""SEC CompanyFacts live-evidence acquisition / SEC CompanyFacts live 근거 수집.

M13 intentionally separates acquisition from canonical evidence. Official SEC data is
captured as a hash-locked SOURCE_SNAPSHOT_CAPTURED object and extraction produces only
EVIDENCE_CANDIDATE_UNREVIEWED. Neither operation writes canonical case state.

M13은 공식 SEC 데이터도 자동으로 정식 FACT로 승격하지 않는다. 원문을 해시 잠금
SOURCE_SNAPSHOT_CAPTURED로 보존하고 추출 결과도 EVIDENCE_CANDIDATE_UNREVIEWED로만
생성한다. 두 단계 모두 정식 사례 상태를 기록하지 않는다.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from valuation_hub.case_service import CaseServiceError, find_repo_root

SNAPSHOT_SCHEMA_VERSION = "source-snapshot-v0.1"
SNAPSHOT_STATUS = "SOURCE_SNAPSHOT_CAPTURED"
SEC_ADAPTER = "sec-companyfacts-v0.1"
SEC_PUBLISHER = "U.S. Securities and Exchange Commission"
SEC_SOURCE_TYPE = "official_edgar_companyfacts_api"
SEC_TIER = "A"
SEC_COMPANYFACTS_HOST = "data.sec.gov"
SEC_REDIRECT_HOSTS = frozenset({"data.sec.gov", "www.sec.gov"})
SEC_MAX_RESPONSE_BYTES = 32 * 1024 * 1024
SEC_TIMEOUT_SECONDS = 20.0
SEC_MIN_REQUEST_INTERVAL_SECONDS = 0.11  # deliberately below 10 requests/sec
CIK_RE = re.compile(r"^[0-9]{1,10}$")
ACCESSION_RE = re.compile(r"^[0-9]{10}-[0-9]{2}-[0-9]{6}$")


@dataclass(frozen=True)
class TransportResponse:
    status: int
    content_type: str
    body: bytes
    final_locator: str
    etag: str | None = None
    last_modified: str | None = None


@dataclass(frozen=True)
class MetricSpec:
    metric: str
    concepts: tuple[tuple[str, str], ...]
    units: tuple[str, ...]
    forms: tuple[str, ...]


METRIC_SPECS: dict[str, MetricSpec] = {
    "revenue": MetricSpec(
        metric="revenue",
        concepts=(
            ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
            ("us-gaap", "Revenues"),
            ("us-gaap", "SalesRevenueNet"),
        ),
        units=("USD",),
        forms=("10-Q", "10-Q/A", "10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"),
    ),
    "operating_income": MetricSpec(
        metric="operating_income",
        concepts=(("us-gaap", "OperatingIncomeLoss"),),
        units=("USD",),
        forms=("10-Q", "10-Q/A", "10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"),
    ),
    "net_income": MetricSpec(
        metric="net_income",
        concepts=(("us-gaap", "NetIncomeLoss"), ("us-gaap", "ProfitLoss")),
        units=("USD",),
        forms=("10-Q", "10-Q/A", "10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"),
    ),
    "assets": MetricSpec(
        metric="assets",
        concepts=(("us-gaap", "Assets"),),
        units=("USD",),
        forms=("10-Q", "10-Q/A", "10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"),
    ),
    "cash": MetricSpec(
        metric="cash",
        concepts=(
            ("us-gaap", "CashAndCashEquivalentsAtCarryingValue"),
            ("us-gaap", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"),
        ),
        units=("USD",),
        forms=("10-Q", "10-Q/A", "10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"),
    ),
    "shares_outstanding": MetricSpec(
        metric="shares_outstanding",
        concepts=(("dei", "EntityCommonStockSharesOutstanding"),),
        units=("shares",),
        forms=("10-Q", "10-Q/A", "10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"),
    ),
}


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _snapshot_hash_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(snapshot)
    payload.pop("snapshot_sha256", None)
    return payload


def normalize_cik(value: str | int) -> str:
    """Return SEC's ten-digit CIK representation / SEC 10자리 CIK 정규화."""
    raw = str(value).strip()
    if not CIK_RE.fullmatch(raw):
        raise CaseServiceError("CIK must contain 1-10 digits / CIK는 1~10자리 숫자여야 합니다")
    return raw.zfill(10)


def companyfacts_locator(cik: str | int) -> str:
    normalized = normalize_cik(cik)
    return f"https://{SEC_COMPANYFACTS_HOST}/api/xbrl/companyfacts/CIK{normalized}.json"


def _validate_sec_locator(locator: str, *, redirect: bool = False) -> None:
    parsed = urlparse(locator)
    allowed = SEC_REDIRECT_HOSTS if redirect else frozenset({SEC_COMPANYFACTS_HOST})
    if parsed.scheme != "https" or parsed.hostname not in allowed:
        raise CaseServiceError("SEC locator must use approved HTTPS host / SEC locator는 승인된 HTTPS host만 허용됩니다")
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise CaseServiceError("SEC locator authority is unsafe / SEC locator authority 오류")


class _SecRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        _validate_sec_locator(newurl, redirect=True)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class SecRateLimiter:
    """Conservative process-local SEC fair-access limiter / 보수적 프로세스 로컬 rate limiter."""

    def __init__(
        self,
        *,
        min_interval: float = SEC_MIN_REQUEST_INTERVAL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if min_interval < 0.1:
            raise ValueError("SEC min_interval must be >= 0.1 seconds")
        self._min_interval = min_interval
        self._clock = clock
        self._sleeper = sleeper
        self._lock = threading.Lock()
        self._last_request: float | None = None

    def acquire(self) -> None:
        with self._lock:
            now = self._clock()
            if self._last_request is not None:
                delay = self._min_interval - (now - self._last_request)
                if delay > 0:
                    self._sleeper(delay)
                    now = self._clock()
            self._last_request = now


_GLOBAL_LIMITER = SecRateLimiter()


def fetch_sec_response(
    locator: str,
    *,
    user_agent: str,
    timeout: float = SEC_TIMEOUT_SECONDS,
    max_bytes: int = SEC_MAX_RESPONSE_BYTES,
    limiter: SecRateLimiter = _GLOBAL_LIMITER,
) -> TransportResponse:
    """Perform one bounded SEC GET. Arbitrary URLs are rejected before network I/O."""
    _validate_sec_locator(locator)
    agent = user_agent.strip()
    if not agent or "@" not in agent or len(agent) < 8:
        raise CaseServiceError(
            "identifying SEC User-Agent with contact email required / 연락 이메일이 포함된 SEC User-Agent가 필요합니다"
        )
    if not 0 < timeout <= 60:
        raise CaseServiceError("SEC timeout must be in (0,60] seconds / SEC timeout 범위 오류")
    if not 1024 <= max_bytes <= SEC_MAX_RESPONSE_BYTES:
        raise CaseServiceError("SEC max_bytes outside safe range / SEC 응답크기 한도 오류")

    limiter.acquire()
    request = Request(
        locator,
        headers={"User-Agent": agent, "Accept": "application/json"},
        method="GET",
    )
    opener = build_opener(_SecRedirectHandler())
    try:
        with opener.open(request, timeout=timeout) as response:
            final_locator = response.geturl()
            _validate_sec_locator(final_locator, redirect=True)
            status = int(getattr(response, "status", response.getcode()))
            content_type = response.headers.get("Content-Type", "")
            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    declared = int(content_length)
                except ValueError as exc:
                    raise CaseServiceError("invalid SEC Content-Length / SEC Content-Length 오류") from exc
                if declared > max_bytes:
                    raise CaseServiceError("SEC response exceeds maximum bytes / SEC 응답이 최대크기를 초과합니다")
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise CaseServiceError("SEC response exceeds maximum bytes / SEC 응답이 최대크기를 초과합니다")
            return TransportResponse(
                status=status,
                content_type=content_type,
                body=body,
                final_locator=final_locator,
                etag=response.headers.get("ETag"),
                last_modified=response.headers.get("Last-Modified"),
            )
    except CaseServiceError:
        raise
    except HTTPError as exc:
        raise CaseServiceError(f"SEC HTTP error / SEC HTTP 오류: {exc.code}") from exc
    except URLError as exc:
        raise CaseServiceError(f"SEC network error / SEC 네트워크 오류: {exc.reason}") from exc
    except OSError as exc:
        raise CaseServiceError(f"SEC transport error / SEC 전송 오류: {exc}") from exc


def _payload_cik(payload: dict[str, Any]) -> str:
    value = payload.get("cik")
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise CaseServiceError("SEC payload CIK missing / SEC payload CIK 누락")
    return normalize_cik(value)


def capture_companyfacts_snapshot(
    cik: str | int,
    *,
    user_agent: str,
    transport: Callable[..., TransportResponse] = fetch_sec_response,
    fetched_at: str | None = None,
) -> dict[str, Any]:
    """Capture a noncanonical, immutable-by-hash CompanyFacts snapshot."""
    normalized = normalize_cik(cik)
    locator = companyfacts_locator(normalized)
    response = transport(locator, user_agent=user_agent)
    if response.status != 200:
        raise CaseServiceError(f"SEC response must be HTTP 200 / SEC HTTP 200 필요: {response.status}")
    _validate_sec_locator(response.final_locator, redirect=True)
    media_type = response.content_type.split(";", 1)[0].strip().lower()
    if media_type not in {"application/json", "application/x-json", "text/json"}:
        raise CaseServiceError(f"SEC response is not JSON / SEC JSON 응답 아님: {response.content_type}")
    if not response.body or len(response.body) > SEC_MAX_RESPONSE_BYTES:
        raise CaseServiceError("SEC response body size invalid / SEC 응답 본문 크기 오류")
    try:
        raw_text = response.body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise CaseServiceError("SEC response is not UTF-8 / SEC 응답 UTF-8 오류") from exc
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise CaseServiceError("SEC response JSON invalid / SEC 응답 JSON 오류") from exc
    if not isinstance(payload, dict):
        raise CaseServiceError("SEC CompanyFacts payload must be object / SEC CompanyFacts 객체 필요")
    if _payload_cik(payload) != normalized:
        raise CaseServiceError("requested CIK does not match SEC payload / 요청 CIK와 SEC payload가 불일치합니다")

    timestamp = fetched_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise CaseServiceError("fetched_at must be ISO-8601 / fetched_at 형식 오류") from exc
    if parsed.tzinfo is None:
        raise CaseServiceError("fetched_at must include timezone / fetched_at에는 시간대가 필요합니다")

    snapshot: dict[str, Any] = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "status": SNAPSHOT_STATUS,
        "canonical": False,
        "adapter": SEC_ADAPTER,
        "source": {
            "publisher": SEC_PUBLISHER,
            "source_type": SEC_SOURCE_TYPE,
            "tier": SEC_TIER,
            "requested_locator": locator,
            "final_locator": response.final_locator,
        },
        "request": {
            "method": "GET",
            "cik": normalized,
            "user_agent_provided": True,
        },
        "response": {
            "http_status": 200,
            "content_type": response.content_type,
            "fetched_at": timestamp,
            "body_bytes": len(response.body),
            "body_sha256": _sha(response.body),
            "etag": response.etag,
            "last_modified": response.last_modified,
        },
        "raw_text": raw_text,
        "snapshot_sha256": "",
    }
    snapshot["snapshot_sha256"] = _sha(_canonical_json_bytes(_snapshot_hash_payload(snapshot)))
    validate_source_snapshot(snapshot)
    return snapshot


def validate_source_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Validate metadata, raw bytes, CIK identity and all snapshot hashes."""
    if not isinstance(snapshot, dict):
        raise CaseServiceError("source snapshot must be object / source snapshot은 객체여야 합니다")
    if snapshot.get("schema_version") != SNAPSHOT_SCHEMA_VERSION or snapshot.get("status") != SNAPSHOT_STATUS:
        raise CaseServiceError("source snapshot schema/status invalid / source snapshot 스키마·상태 오류")
    if snapshot.get("canonical") is not False or snapshot.get("adapter") != SEC_ADAPTER:
        raise CaseServiceError("source snapshot canonical/adapter invalid / source snapshot 정식상태·adapter 오류")
    source = snapshot.get("source")
    request = snapshot.get("request")
    response = snapshot.get("response")
    raw_text = snapshot.get("raw_text")
    if not isinstance(source, dict) or not isinstance(request, dict) or not isinstance(response, dict) or not isinstance(raw_text, str):
        raise CaseServiceError("source snapshot structure invalid / source snapshot 구조 오류")
    if source.get("publisher") != SEC_PUBLISHER or source.get("source_type") != SEC_SOURCE_TYPE or source.get("tier") != SEC_TIER:
        raise CaseServiceError("SEC source identity invalid / SEC 출처 식별 오류")
    _validate_sec_locator(str(source.get("requested_locator", "")))
    _validate_sec_locator(str(source.get("final_locator", "")), redirect=True)
    cik = normalize_cik(str(request.get("cik", "")))
    if request.get("method") != "GET" or request.get("user_agent_provided") is not True:
        raise CaseServiceError("SEC request metadata invalid / SEC 요청 메타데이터 오류")
    if source.get("requested_locator") != companyfacts_locator(cik):
        raise CaseServiceError("SEC requested locator/CIK mismatch / SEC 요청 locator·CIK 불일치")
    if response.get("http_status") != 200:
        raise CaseServiceError("source snapshot requires HTTP 200 / source snapshot HTTP 200 필요")
    fetched_at = response.get("fetched_at")
    if not isinstance(fetched_at, str):
        raise CaseServiceError("snapshot fetched_at missing / snapshot fetched_at 누락")
    try:
        parsed_time = datetime.fromisoformat(fetched_at)
    except ValueError as exc:
        raise CaseServiceError("snapshot fetched_at invalid / snapshot fetched_at 오류") from exc
    if parsed_time.tzinfo is None:
        raise CaseServiceError("snapshot fetched_at timezone missing / snapshot fetched_at 시간대 누락")

    raw_bytes = raw_text.encode("utf-8")
    if response.get("body_bytes") != len(raw_bytes) or response.get("body_sha256") != _sha(raw_bytes):
        raise CaseServiceError("source snapshot raw body hash/size mismatch / source snapshot 원문 해시·크기 불일치")
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise CaseServiceError("snapshot raw JSON invalid / snapshot 원문 JSON 오류") from exc
    if not isinstance(payload, dict) or _payload_cik(payload) != cik:
        raise CaseServiceError("snapshot payload CIK mismatch / snapshot payload CIK 불일치")
    expected_hash = _sha(_canonical_json_bytes(_snapshot_hash_payload(snapshot)))
    if snapshot.get("snapshot_sha256") != expected_hash:
        raise CaseServiceError("source snapshot SHA-256 mismatch / source snapshot SHA-256 불일치")
    return {
        "status": "PASS_SOURCE_SNAPSHOT_VALIDATION",
        "canonical": False,
        "adapter": SEC_ADAPTER,
        "cik": cik,
        "body_sha256": response["body_sha256"],
        "snapshot_sha256": expected_hash,
        "fetched_at": fetched_at,
    }


def _parse_snapshot_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
    validate_source_snapshot(snapshot)
    payload = json.loads(snapshot["raw_text"])
    if not isinstance(payload, dict):
        raise CaseServiceError("snapshot payload object required / snapshot payload 객체 필요")
    return payload


def _valid_iso_date(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise CaseServiceError(f"SEC fact {field} must be date string / SEC fact {field} 날짜 형식 오류")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise CaseServiceError(f"SEC fact {field} invalid / SEC fact {field} 오류: {value}") from exc
    return parsed.isoformat()


def _fact_value_key(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise CaseServiceError("SEC fact value is not JSON-safe / SEC fact 값 형식 오류") from exc


def extract_sec_evidence_candidate(
    snapshot: dict[str, Any],
    metric: str,
    *,
    form: str | None = None,
    period_end: str | None = None,
) -> dict[str, Any]:
    """Select one filing-grounded fact without normalization or TTM synthesis.

    Concept fallback is explicit. Within the first concept containing admissible facts,
    the newest filed date and newest period end are selected. If multiple facts remain
    at identical precedence with conflicting values, extraction fails closed.
    """
    payload = _parse_snapshot_payload(snapshot)
    spec = METRIC_SPECS.get(metric)
    if spec is None:
        raise CaseServiceError(f"unsupported SEC metric / 미지원 SEC 지표: {metric}")
    requested_form = form.upper() if form else None
    if requested_form is not None and requested_form not in spec.forms:
        raise CaseServiceError(f"form not allowed for metric / 지표에 허용되지 않은 form: {requested_form}")
    requested_end = _valid_iso_date(period_end, "period_end") if period_end else None

    facts_root = payload.get("facts")
    if not isinstance(facts_root, dict):
        raise CaseServiceError("SEC CompanyFacts facts object missing / SEC CompanyFacts facts 누락")

    selected_concept: tuple[str, str] | None = None
    candidates: list[dict[str, Any]] = []
    fallback_index = -1
    selected_unit = ""
    for index, (taxonomy, concept) in enumerate(spec.concepts):
        taxonomy_obj = facts_root.get(taxonomy)
        concept_obj = taxonomy_obj.get(concept) if isinstance(taxonomy_obj, dict) else None
        units_obj = concept_obj.get("units") if isinstance(concept_obj, dict) else None
        if not isinstance(units_obj, dict):
            continue
        concept_candidates: list[dict[str, Any]] = []
        concept_unit = ""
        for unit in spec.units:
            series = units_obj.get(unit)
            if not isinstance(series, list):
                continue
            for raw in series:
                if not isinstance(raw, dict):
                    continue
                raw_form = raw.get("form")
                if raw_form not in spec.forms or (requested_form and raw_form != requested_form):
                    continue
                end = _valid_iso_date(raw.get("end"), "end")
                if requested_end and end != requested_end:
                    continue
                filed = _valid_iso_date(raw.get("filed"), "filed")
                if not filed or not end:
                    continue
                accn = raw.get("accn")
                if not isinstance(accn, str) or not ACCESSION_RE.fullmatch(accn):
                    raise CaseServiceError("SEC fact accession invalid / SEC fact accession 오류")
                if "val" not in raw:
                    continue
                fact = copy.deepcopy(raw)
                fact["filed"] = filed
                fact["end"] = end
                if "start" in fact:
                    fact["start"] = _valid_iso_date(fact.get("start"), "start")
                concept_candidates.append(fact)
                concept_unit = unit
        if concept_candidates:
            selected_concept = (taxonomy, concept)
            candidates = concept_candidates
            fallback_index = index
            selected_unit = concept_unit
            break

    if selected_concept is None or not candidates:
        filters = f"form={requested_form or '*'}, period_end={requested_end or '*'}"
        raise CaseServiceError(f"no SEC fact matches metric/filter / SEC 지표·필터 일치 fact 없음: {metric} ({filters})")

    latest_filed = max(item["filed"] for item in candidates)
    top = [item for item in candidates if item["filed"] == latest_filed]
    latest_end = max(item["end"] for item in top)
    top = [item for item in top if item["end"] == latest_end]
    distinct_values = {_fact_value_key(item.get("val")) for item in top}
    if len(distinct_values) != 1:
        raise CaseServiceError(
            "ambiguous SEC facts at equal precedence; add form/period filter / 동일 우선순위 SEC fact 값 충돌: form 또는 기간 필터가 필요합니다"
        )
    # Duplicate representations with the same value are semantically equivalent for M13.
    chosen = sorted(
        top,
        key=lambda item: (
            str(item.get("accn", "")),
            str(item.get("form", "")),
            str(item.get("start", "")),
            str(item.get("frame", "")),
        ),
        reverse=True,
    )[0]
    taxonomy, concept = selected_concept
    source_locator = snapshot["source"]["final_locator"]
    candidate = {
        "schema_version": "sec-evidence-candidate-v0.1",
        "status": "EVIDENCE_CANDIDATE_UNREVIEWED",
        "canonical": False,
        "class": "FACT_CANDIDATE",
        "metric": metric,
        "value": chosen["val"],
        "unit": selected_unit,
        "period": {
            "start": chosen.get("start"),
            "end": chosen["end"],
            "fy": chosen.get("fy"),
            "fp": chosen.get("fp"),
            "frame": chosen.get("frame"),
        },
        "filing": {
            "accession": chosen["accn"],
            "form": chosen["form"],
            "filed": chosen["filed"],
        },
        "taxonomy": taxonomy,
        "concept": concept,
        "concept_fallback_index": fallback_index,
        "concept_fallback_used": fallback_index > 0,
        "source": {
            "publisher": SEC_PUBLISHER,
            "source_type": SEC_SOURCE_TYPE,
            "tier_proposal": SEC_TIER,
            "locator": source_locator,
            "snapshot_sha256": snapshot["snapshot_sha256"],
            "body_sha256": snapshot["response"]["body_sha256"],
        },
        "selection": {
            "rule": "FIRST_AVAILABLE_CONCEPT_THEN_LATEST_FILED_THEN_LATEST_END",
            "requested_form": requested_form,
            "requested_period_end": requested_end,
            "equal_precedence_count": len(top),
        },
        "warning_en": "Unreviewed evidence candidate. It is not canonical and must pass existing governance/review before FACT admission.",
        "warning_ko": "미검토 근거 후보입니다. 정식 FACT가 아니며 기존 거버넌스·검토 절차를 통과해야 합니다.",
    }
    return candidate


def materialize_source_snapshot(
    snapshot: dict[str, Any],
    output: Path,
    root: Path | None = None,
) -> dict[str, Any]:
    """Write one validated snapshot below workspace/source_snapshots without overwrite."""
    repo = root.resolve() if root else find_repo_root()
    validate_source_snapshot(snapshot)
    target = output.resolve()
    allowed = (repo / "workspace" / "source_snapshots").resolve()
    try:
        target.relative_to(allowed)
    except ValueError as exc:
        raise CaseServiceError(
            "source snapshots may only be written under workspace/source_snapshots / source snapshot은 workspace/source_snapshots 아래에만 기록할 수 있습니다"
        ) from exc
    if target.exists():
        raise CaseServiceError("source snapshot output already exists / source snapshot 출력파일이 이미 존재합니다")
    target.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(target, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            target.unlink(missing_ok=True)
        finally:
            raise
    return {
        "status": "SOURCE_SNAPSHOT_MATERIALIZED",
        "canonical": False,
        "path": str(target),
        "snapshot_sha256": snapshot["snapshot_sha256"],
        "file_sha256": _sha(data),
    }


def load_source_snapshot(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaseServiceError(f"source snapshot file not found / source snapshot 파일 없음: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseServiceError(f"source snapshot read failed / source snapshot 읽기 실패: {path}") from exc
    if not isinstance(payload, dict):
        raise CaseServiceError("source snapshot file must contain object / source snapshot 파일은 객체여야 합니다")
    return payload
