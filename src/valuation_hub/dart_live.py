"""OpenDART immutable live-evidence acquisition / OpenDART 불변 live 근거수집.

M14 mirrors the M13 authority boundary for Korea FSS OpenDART. Authentication is a
transport secret only: the API key must never survive into snapshots, locators,
errors, Web payloads, or evidence candidates.
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from valuation_hub.case_service import CaseServiceError, find_repo_root

DART_SNAPSHOT_SCHEMA_VERSION = "dart-source-snapshot-v0.1"
DART_SNAPSHOT_STATUS = "SOURCE_SNAPSHOT_CAPTURED"
DART_ADAPTER = "opendart-fnltt-singl-acnt-all-v0.1"
DART_PUBLISHER = "Financial Supervisory Service, Republic of Korea"
DART_SOURCE_TYPE = "official_opendart_financial_statements_api"
DART_TIER = "A"
DART_HOST = "opendart.fss.or.kr"
DART_PATH = "/api/fnlttSinglAcntAll.json"
DART_MAX_RESPONSE_BYTES = 16 * 1024 * 1024
DART_TIMEOUT_SECONDS = 20.0
DART_MIN_REQUEST_INTERVAL_SECONDS = 0.11
REPORT_CODES = frozenset({"11013", "11012", "11014", "11011"})
FS_DIVS = frozenset({"CFS", "OFS"})
CORP_CODE_RE = re.compile(r"^[0-9]{8}$")
YEAR_RE = re.compile(r"^[0-9]{4}$")
API_KEY_RE = re.compile(r"^[^\s]{20,128}$")


@dataclass(frozen=True)
class DartTransportResponse:
    status: int
    content_type: str
    body: bytes
    sanitized_final_locator: str
    etag: str | None = None
    last_modified: str | None = None


@dataclass(frozen=True)
class DartMetricSpec:
    metric: str
    statement_sections: tuple[str, ...]
    account_ids: tuple[str, ...]
    account_names: tuple[str, ...]


DART_METRIC_SPECS: dict[str, DartMetricSpec] = {
    "revenue": DartMetricSpec(
        "revenue",
        ("IS", "CIS"),
        ("ifrs-full_Revenue",),
        ("매출액", "수익(매출액)"),
    ),
    "operating_income": DartMetricSpec(
        "operating_income",
        ("IS", "CIS"),
        ("dart_OperatingIncomeLoss", "ifrs-full_ProfitLossFromOperatingActivities"),
        ("영업이익", "영업이익(손실)"),
    ),
    "net_income": DartMetricSpec(
        "net_income",
        ("IS", "CIS"),
        ("ifrs-full_ProfitLoss",),
        ("당기순이익", "당기순이익(손실)", "분기순이익", "반기순이익"),
    ),
    "assets": DartMetricSpec(
        "assets",
        ("BS",),
        ("ifrs-full_Assets",),
        ("자산총계",),
    ),
    "cash": DartMetricSpec(
        "cash",
        ("BS",),
        ("ifrs-full_CashAndCashEquivalents",),
        ("현금및현금성자산", "현금 및 현금성자산"),
    ),
    "equity": DartMetricSpec(
        "equity",
        ("BS",),
        ("ifrs-full_Equity",),
        ("자본총계",),
    ),
    "liabilities": DartMetricSpec(
        "liabilities",
        ("BS",),
        ("ifrs-full_Liabilities",),
        ("부채총계",),
    ),
}


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _snapshot_hash_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(snapshot)
    payload.pop("snapshot_sha256", None)
    return payload


def _validate_request_identity(corp_code: str, bsns_year: str | int, reprt_code: str, fs_div: str) -> tuple[str, str, str, str]:
    corp = str(corp_code).strip()
    year = str(bsns_year).strip()
    report = str(reprt_code).strip()
    division = str(fs_div).strip().upper()
    if not CORP_CODE_RE.fullmatch(corp):
        raise CaseServiceError("OpenDART corp_code must be 8 digits / OpenDART corp_code는 8자리 숫자여야 합니다")
    if not YEAR_RE.fullmatch(year) or not 1990 <= int(year) <= 2100:
        raise CaseServiceError("OpenDART bsns_year invalid / OpenDART bsns_year 오류")
    if report not in REPORT_CODES:
        raise CaseServiceError("OpenDART reprt_code invalid / OpenDART reprt_code 오류")
    if division not in FS_DIVS:
        raise CaseServiceError("OpenDART fs_div must be CFS or OFS / OpenDART fs_div는 CFS 또는 OFS여야 합니다")
    return corp, year, report, division


def _validate_api_key(api_key: str) -> str:
    key = str(api_key).strip()
    if not API_KEY_RE.fullmatch(key):
        raise CaseServiceError("valid OpenDART API key required / 유효한 OpenDART API key가 필요합니다")
    return key


def dart_sanitized_locator(corp_code: str, bsns_year: str | int, reprt_code: str, fs_div: str) -> str:
    corp, year, report, division = _validate_request_identity(corp_code, bsns_year, reprt_code, fs_div)
    query = urlencode({"corp_code": corp, "bsns_year": year, "reprt_code": report, "fs_div": division})
    return f"https://{DART_HOST}{DART_PATH}?{query}"


def _actual_locator(sanitized_locator: str, api_key: str) -> str:
    parsed = urlparse(sanitized_locator)
    query = parse_qs(parsed.query, keep_blank_values=True)
    query["crtfc_key"] = [_validate_api_key(api_key)]
    encoded = urlencode([(key, value) for key, values in query.items() for value in values])
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", encoded, ""))


def _sanitize_locator(locator: str) -> str:
    parsed = urlparse(locator)
    if parsed.scheme != "https" or parsed.hostname != DART_HOST or parsed.path != DART_PATH:
        raise CaseServiceError("OpenDART locator must use approved HTTPS endpoint / OpenDART locator는 승인된 HTTPS endpoint만 허용됩니다")
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise CaseServiceError("OpenDART locator authority invalid / OpenDART locator authority 오류")
    query = parse_qs(parsed.query, keep_blank_values=True)
    allowed = {"corp_code", "bsns_year", "reprt_code", "fs_div", "crtfc_key"}
    if set(query) - allowed:
        raise CaseServiceError("OpenDART locator query invalid / OpenDART locator query 오류")
    required = {"corp_code", "bsns_year", "reprt_code", "fs_div"}
    if not required.issubset(query) or any(len(query[name]) != 1 for name in required):
        raise CaseServiceError("OpenDART locator identity missing / OpenDART locator 식별자 누락")
    return dart_sanitized_locator(query["corp_code"][0], query["bsns_year"][0], query["reprt_code"][0], query["fs_div"][0])


class _DartRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        _sanitize_locator(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class DartRateLimiter:
    def __init__(self, *, min_interval: float = DART_MIN_REQUEST_INTERVAL_SECONDS, clock: Callable[[], float] = time.monotonic, sleeper: Callable[[float], None] = time.sleep) -> None:
        if min_interval < 0.1:
            raise ValueError("OpenDART min_interval must be >= 0.1 seconds")
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


_GLOBAL_LIMITER = DartRateLimiter()


def fetch_dart_response(sanitized_locator: str, *, api_key: str, timeout: float = DART_TIMEOUT_SECONDS, max_bytes: int = DART_MAX_RESPONSE_BYTES, limiter: DartRateLimiter = _GLOBAL_LIMITER) -> DartTransportResponse:
    """Fetch one OpenDART response while keeping the authentication key inside transport."""
    sanitized = _sanitize_locator(sanitized_locator)
    key = _validate_api_key(api_key)
    if not 0 < timeout <= 60:
        raise CaseServiceError("OpenDART timeout outside safe range / OpenDART timeout 범위 오류")
    if not 1024 <= max_bytes <= DART_MAX_RESPONSE_BYTES:
        raise CaseServiceError("OpenDART max_bytes outside safe range / OpenDART 응답크기 한도 오류")
    locator = _actual_locator(sanitized, key)
    limiter.acquire()
    request = Request(locator, headers={"Accept": "application/json"}, method="GET")
    opener = build_opener(_DartRedirectHandler())
    try:
        with opener.open(request, timeout=timeout) as response:
            final_locator = response.geturl()
            sanitized_final = _sanitize_locator(final_locator)
            status = int(getattr(response, "status", response.getcode()))
            content_type = response.headers.get("Content-Type", "")
            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    declared = int(content_length)
                except ValueError as exc:
                    raise CaseServiceError("invalid OpenDART Content-Length / OpenDART Content-Length 오류") from exc
                if declared > max_bytes:
                    raise CaseServiceError("OpenDART response exceeds maximum bytes / OpenDART 응답이 최대크기를 초과합니다")
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise CaseServiceError("OpenDART response exceeds maximum bytes / OpenDART 응답이 최대크기를 초과합니다")
            return DartTransportResponse(status, content_type, body, sanitized_final, response.headers.get("ETag"), response.headers.get("Last-Modified"))
    except CaseServiceError:
        raise
    except HTTPError as exc:
        raise CaseServiceError(f"OpenDART HTTP error / OpenDART HTTP 오류: {exc.code}") from exc
    except URLError as exc:
        raise CaseServiceError("OpenDART network error / OpenDART 네트워크 오류") from exc
    except OSError as exc:
        raise CaseServiceError("OpenDART transport error / OpenDART 전송 오류") from exc


def _validate_api_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    status = payload.get("status")
    if status != "000":
        message = payload.get("message")
        safe_message = str(message)[:160] if isinstance(message, str) else "unknown"
        raise CaseServiceError(f"OpenDART API status {status}: {safe_message}")
    rows = payload.get("list")
    if not isinstance(rows, list):
        raise CaseServiceError("OpenDART success payload requires list / OpenDART 성공 응답 list 누락")
    if not all(isinstance(row, dict) for row in rows):
        raise CaseServiceError("OpenDART list rows malformed / OpenDART list row 구조 오류")
    return rows


def capture_dart_snapshot(corp_code: str, bsns_year: str | int, reprt_code: str, fs_div: str, *, api_key: str, transport: Callable[..., DartTransportResponse] = fetch_dart_response, fetched_at: str | None = None) -> dict[str, Any]:
    corp, year, report, division = _validate_request_identity(corp_code, bsns_year, reprt_code, fs_div)
    _validate_api_key(api_key)
    sanitized = dart_sanitized_locator(corp, year, report, division)
    response = transport(sanitized, api_key=api_key)
    if response.status != 200:
        raise CaseServiceError(f"OpenDART response must be HTTP 200 / OpenDART HTTP 200 필요: {response.status}")
    if _sanitize_locator(response.sanitized_final_locator) != sanitized:
        raise CaseServiceError("OpenDART final request identity changed / OpenDART 최종 요청 식별자가 변경되었습니다")
    media_type = response.content_type.split(";", 1)[0].strip().lower()
    if media_type not in {"application/json", "application/x-json", "text/json"}:
        raise CaseServiceError("OpenDART response is not JSON / OpenDART JSON 응답 아님")
    if not response.body or len(response.body) > DART_MAX_RESPONSE_BYTES:
        raise CaseServiceError("OpenDART response body size invalid / OpenDART 응답 본문 크기 오류")
    try:
        raw_text = response.body.decode("utf-8", errors="strict")
        payload = json.loads(raw_text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CaseServiceError("OpenDART response UTF-8/JSON invalid / OpenDART 응답 UTF-8/JSON 오류") from exc
    if not isinstance(payload, dict):
        raise CaseServiceError("OpenDART payload must be object / OpenDART payload 객체 필요")
    rows = _validate_api_payload(payload)
    for row in rows:
        if row.get("corp_code") not in (None, "", corp):
            raise CaseServiceError("OpenDART row corp_code mismatch / OpenDART row corp_code 불일치")
        if row.get("bsns_year") not in (None, "", year):
            raise CaseServiceError("OpenDART row bsns_year mismatch / OpenDART row bsns_year 불일치")
        if row.get("reprt_code") not in (None, "", report):
            raise CaseServiceError("OpenDART row reprt_code mismatch / OpenDART row reprt_code 불일치")
        if row.get("fs_div") not in (None, "", division):
            raise CaseServiceError("OpenDART row fs_div mismatch / OpenDART row fs_div 불일치")
    timestamp = fetched_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise CaseServiceError("fetched_at must be ISO-8601 / fetched_at 형식 오류") from exc
    if parsed.tzinfo is None:
        raise CaseServiceError("fetched_at must include timezone / fetched_at 시간대 누락")
    snapshot: dict[str, Any] = {
        "schema_version": DART_SNAPSHOT_SCHEMA_VERSION,
        "status": DART_SNAPSHOT_STATUS,
        "canonical": False,
        "adapter": DART_ADAPTER,
        "source": {
            "publisher": DART_PUBLISHER,
            "source_type": DART_SOURCE_TYPE,
            "tier": DART_TIER,
            "requested_locator": sanitized,
            "final_locator": response.sanitized_final_locator,
        },
        "request": {
            "method": "GET",
            "corp_code": corp,
            "bsns_year": year,
            "reprt_code": report,
            "fs_div": division,
            "api_key_provided": True,
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
    if api_key in json.dumps(snapshot, ensure_ascii=False):
        raise CaseServiceError("OpenDART API key leakage detected / OpenDART API key 노출 감지")
    snapshot["snapshot_sha256"] = _sha(_canonical_json_bytes(_snapshot_hash_payload(snapshot)))
    validate_dart_snapshot(snapshot)
    return snapshot


def validate_dart_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        raise CaseServiceError("OpenDART snapshot must be object / OpenDART snapshot 객체 필요")
    if snapshot.get("schema_version") != DART_SNAPSHOT_SCHEMA_VERSION or snapshot.get("status") != DART_SNAPSHOT_STATUS:
        raise CaseServiceError("OpenDART snapshot schema/status invalid / OpenDART snapshot 스키마·상태 오류")
    if snapshot.get("canonical") is not False or snapshot.get("adapter") != DART_ADAPTER:
        raise CaseServiceError("OpenDART snapshot canonical/adapter invalid / OpenDART snapshot 정식상태·adapter 오류")
    source, request, response, raw_text = snapshot.get("source"), snapshot.get("request"), snapshot.get("response"), snapshot.get("raw_text")
    if not isinstance(source, dict) or not isinstance(request, dict) or not isinstance(response, dict) or not isinstance(raw_text, str):
        raise CaseServiceError("OpenDART snapshot structure invalid / OpenDART snapshot 구조 오류")
    if source.get("publisher") != DART_PUBLISHER or source.get("source_type") != DART_SOURCE_TYPE or source.get("tier") != DART_TIER:
        raise CaseServiceError("OpenDART source identity invalid / OpenDART 출처 식별 오류")
    corp, year, report, division = _validate_request_identity(request.get("corp_code", ""), request.get("bsns_year", ""), request.get("reprt_code", ""), request.get("fs_div", ""))
    if request.get("method") != "GET" or request.get("api_key_provided") is not True:
        raise CaseServiceError("OpenDART request metadata invalid / OpenDART 요청 메타데이터 오류")
    expected_locator = dart_sanitized_locator(corp, year, report, division)
    if _sanitize_locator(str(source.get("requested_locator", ""))) != expected_locator or _sanitize_locator(str(source.get("final_locator", ""))) != expected_locator:
        raise CaseServiceError("OpenDART snapshot locator mismatch / OpenDART snapshot locator 불일치")
    if "crtfc_key" in str(source.get("requested_locator")) or "crtfc_key" in str(source.get("final_locator")):
        raise CaseServiceError("OpenDART snapshot contains secret query / OpenDART snapshot secret query 노출")
    if response.get("http_status") != 200:
        raise CaseServiceError("OpenDART snapshot requires HTTP 200 / OpenDART snapshot HTTP 200 필요")
    fetched_at = response.get("fetched_at")
    if not isinstance(fetched_at, str):
        raise CaseServiceError("OpenDART snapshot fetched_at missing / OpenDART snapshot fetched_at 누락")
    try:
        parsed = datetime.fromisoformat(fetched_at)
    except ValueError as exc:
        raise CaseServiceError("OpenDART snapshot fetched_at invalid / OpenDART snapshot fetched_at 오류") from exc
    if parsed.tzinfo is None:
        raise CaseServiceError("OpenDART snapshot fetched_at timezone missing / OpenDART snapshot fetched_at 시간대 누락")
    raw_bytes = raw_text.encode("utf-8")
    if response.get("body_bytes") != len(raw_bytes) or response.get("body_sha256") != _sha(raw_bytes):
        raise CaseServiceError("OpenDART raw body hash/size mismatch / OpenDART 원문 해시·크기 불일치")
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise CaseServiceError("OpenDART snapshot raw JSON invalid / OpenDART snapshot 원문 JSON 오류") from exc
    if not isinstance(payload, dict):
        raise CaseServiceError("OpenDART snapshot payload invalid / OpenDART snapshot payload 오류")
    rows = _validate_api_payload(payload)
    for row in rows:
        if row.get("corp_code") not in (None, "", corp) or row.get("bsns_year") not in (None, "", year) or row.get("reprt_code") not in (None, "", report) or row.get("fs_div") not in (None, "", division):
            raise CaseServiceError("OpenDART snapshot row identity mismatch / OpenDART snapshot row 식별 불일치")
    expected_hash = _sha(_canonical_json_bytes(_snapshot_hash_payload(snapshot)))
    if snapshot.get("snapshot_sha256") != expected_hash:
        raise CaseServiceError("OpenDART snapshot SHA-256 mismatch / OpenDART snapshot SHA-256 불일치")
    return {"status": "PASS_DART_SOURCE_SNAPSHOT_VALIDATION", "canonical": False, "adapter": DART_ADAPTER, "corp_code": corp, "bsns_year": year, "reprt_code": report, "fs_div": division, "body_sha256": response["body_sha256"], "snapshot_sha256": expected_hash, "fetched_at": fetched_at}


def _parse_amount(raw: Any) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        raise CaseServiceError("OpenDART amount invalid / OpenDART 금액 오류")
    if isinstance(raw, int):
        return raw
    if not isinstance(raw, str):
        raise CaseServiceError("OpenDART amount must be string/integer / OpenDART 금액 형식 오류")
    text = raw.strip()
    if text in {"", "-"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1].strip()
    compact = text.replace(",", "")
    if not re.fullmatch(r"[-+]?[0-9]+", compact):
        raise CaseServiceError(f"OpenDART amount is not an integer / OpenDART 금액 숫자 오류: {raw}")
    value = int(compact)
    return -abs(value) if negative else value


def extract_dart_evidence_candidate(snapshot: dict[str, Any], metric: str, *, statement_section: str | None = None) -> dict[str, Any]:
    validation = validate_dart_snapshot(snapshot)
    spec = DART_METRIC_SPECS.get(metric)
    if spec is None:
        raise CaseServiceError(f"unsupported OpenDART metric / 미지원 OpenDART 지표: {metric}")
    requested_section = statement_section.upper() if statement_section else None
    if requested_section and requested_section not in spec.statement_sections:
        raise CaseServiceError("statement section not allowed for metric / 지표에 허용되지 않은 재무제표 구분")
    payload = json.loads(snapshot["raw_text"])
    rows: list[dict[str, Any]] = payload["list"]
    sections = (requested_section,) if requested_section else spec.statement_sections
    selected: list[dict[str, Any]] = []
    selection_kind = ""
    fallback_index = -1
    selected_section = ""
    for section_index, section in enumerate(sections):
        section_rows = [row for row in rows if str(row.get("sj_div", "")).upper() == section]
        if not section_rows:
            continue
        for idx, account_id in enumerate(spec.account_ids):
            matches = [row for row in section_rows if row.get("account_id") == account_id]
            if matches:
                selected, selection_kind, fallback_index, selected_section = matches, "account_id", idx, section
                break
        if selected:
            break
        for idx, account_name in enumerate(spec.account_names):
            matches = [row for row in section_rows if row.get("account_nm") == account_name]
            if matches:
                selected, selection_kind, fallback_index, selected_section = matches, "account_nm", len(spec.account_ids) + idx, section
                break
        if selected:
            break
    if not selected:
        raise CaseServiceError(f"no OpenDART row matches metric / OpenDART 지표 일치 row 없음: {metric}")
    parsed_values = {_parse_amount(row.get("thstrm_amount")) for row in selected}
    non_null_values = {value for value in parsed_values if value is not None}
    if len(non_null_values) > 1:
        raise CaseServiceError("equal-precedence OpenDART rows conflict / 동일 우선순위 OpenDART row 값 충돌")
    if not non_null_values:
        raise CaseServiceError("OpenDART current-period amount is blank/unknown / OpenDART 당기 금액이 공란·미상입니다")
    value = next(iter(non_null_values))
    chosen = sorted(selected, key=lambda row: (str(row.get("rcept_no", "")), str(row.get("ord", "")), str(row.get("account_detail", ""))), reverse=True)[0]
    provenance_fields = ("rcept_no", "reprt_code", "bsns_year", "corp_code", "stock_code", "fs_div", "fs_nm", "sj_div", "sj_nm", "account_id", "account_nm", "account_detail", "thstrm_nm", "thstrm_amount", "thstrm_add_amount", "frmtrm_nm", "frmtrm_amount", "bfefrmtrm_nm", "bfefrmtrm_amount", "ord", "currency")
    row_provenance = {name: chosen.get(name) for name in provenance_fields}
    return {
        "schema_version": "dart-evidence-candidate-v0.1",
        "status": "DART_EVIDENCE_CANDIDATE_UNREVIEWED",
        "canonical": False,
        "class": "FACT_CANDIDATE",
        "metric": metric,
        "value": value,
        "unit": chosen.get("currency") or "KRW",
        "request_identity": {"corp_code": validation["corp_code"], "bsns_year": validation["bsns_year"], "reprt_code": validation["reprt_code"], "fs_div": validation["fs_div"]},
        "statement_section": selected_section,
        "account_selection": {"kind": selection_kind, "fallback_index": fallback_index, "fallback_used": fallback_index > 0 or selection_kind == "account_nm", "requested_statement_section": requested_section, "equal_precedence_count": len(selected)},
        "row": row_provenance,
        "source": {"publisher": DART_PUBLISHER, "source_type": DART_SOURCE_TYPE, "tier_proposal": DART_TIER, "locator": snapshot["source"]["final_locator"], "snapshot_sha256": snapshot["snapshot_sha256"], "body_sha256": snapshot["response"]["body_sha256"]},
        "warning_en": "Unreviewed OpenDART evidence candidate. It is not canonical and must pass existing governance/review before FACT admission.",
        "warning_ko": "미검토 OpenDART 근거 후보입니다. 정식 FACT가 아니며 기존 거버넌스·검토를 통과해야 합니다.",
    }


def materialize_dart_snapshot(snapshot: dict[str, Any], output: Path, root: Path | None = None) -> dict[str, Any]:
    repo = root.resolve() if root else find_repo_root()
    validate_dart_snapshot(snapshot)
    target = output.resolve()
    allowed = (repo / "workspace" / "source_snapshots").resolve()
    try:
        target.relative_to(allowed)
    except ValueError as exc:
        raise CaseServiceError("OpenDART snapshots may only be written under workspace/source_snapshots / OpenDART snapshot은 workspace/source_snapshots 아래에만 기록할 수 있습니다") from exc
    if target.exists():
        raise CaseServiceError("OpenDART snapshot output already exists / OpenDART snapshot 출력파일이 이미 존재합니다")
    target.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return {"status": "DART_SOURCE_SNAPSHOT_MATERIALIZED", "canonical": False, "path": str(target), "snapshot_sha256": snapshot["snapshot_sha256"], "file_sha256": _sha(data)}


def load_dart_snapshot(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaseServiceError(f"OpenDART snapshot file not found / OpenDART snapshot 파일 없음: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseServiceError(f"OpenDART snapshot read failed / OpenDART snapshot 읽기 실패: {path}") from exc
    if not isinstance(payload, dict):
        raise CaseServiceError("OpenDART snapshot file must contain object / OpenDART snapshot 파일은 객체여야 합니다")
    return payload
