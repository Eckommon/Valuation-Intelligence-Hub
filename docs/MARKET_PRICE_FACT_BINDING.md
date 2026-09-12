# M27 Governed Market Price FACT Binding / M27 거버넌스 시장가격 FACT 바인딩

## Purpose / 목적

M27 converts an exact valuation-date market quote into a governed, source-backed market `FACT` and integrates only a reviewed eligible package into the equity-FCFF Draft as `market_price`.

M27은 가치평가일 시장 quote를 출처가 잠긴 시장 `FACT`로 거버넌스하고, 검토완료 적격 패키지만 equity-FCFF Draft의 `market_price`로 연결한다.

## Authority boundary / 권위경계

```text
quoted number without provenance != governed market-price FACT
historical adjusted price != valuation-date market price
FACT_CANDIDATE != FACT
reviewed FACT != canonical state
```

Market price is an observed fact, not a valuation assumption.

시장가격은 관측사실이며 가치평가 가정이 아니다.

## Required quote identity / 필수 Quote 식별

v0.1 requires:

- positive as-traded price per share
- quote currency
- exact trading date
- timezone-aware quote observation timestamp
- entity ID + financial scope
- security/instrument ID + symbol
- trading venue
- security type `COMMON_EQUITY`
- explicit quote type `OFFICIAL_CLOSE` or `LAST_TRADE`
- exact price basis `AS_TRADED_PER_SHARE`
- valuation `as_of`
- source publisher/type/tier/locator
- source snapshot SHA-256

No quote type, venue, corporate-action transform, or date substitution is inferred.

Quote 유형, 거래소, 기업행위 변환, 날짜대체를 추론하지 않는다.

## Freshness / 최신성

```text
0 <= max_age_days <= 30
age_days = as_of - trading_date
```

Trading dates after valuation `as_of` fail closed. Stale quotes remain visible but cannot become review-eligible.

Weekend or holiday valuation dates may use an explicitly supplied prior trading date only within the stated freshness bound.

## Corporate-action boundary / 기업행위 경계

M27 v0.1 governs only the security price **as traded at the quoted timestamp**.

```text
historical_price_substitution = false
split_adjustment_performed = false
```

Historical split-adjusted price normalization belongs to a separate explicit transform and is never silently performed by M27.

## Human review / 인간검토

Lifecycle:

```text
source-backed quote
  ↓
FACT_CANDIDATE
  ↓
SHA-locked human review assertion
  ↓
reviewed noncanonical FACT
```

Review requires Tier A/B source and fresh quote evidence. The assertion locks the candidate SHA, source snapshot SHA, quote identity, freshness policy, reviewer, timestamp, and review basis.

Chronology is fail-closed:

```text
approved_at >= observed_at
approved_at.date >= valuation as_of
```

A quote cannot be approved before it has actually been observed. Re-signing an outer assertion SHA cannot bypass this rule because validation independently recomputes chronology.

## v0.7 Draft binding / v0.7 Draft 바인딩

```text
validated draft-binding-proposal-v0.6
        +
reviewed fresh market-price FACT
        ↓
draft-binding-proposal-v0.7
```

M27 accepts only a validated v0.6 base proposal and may replace only:

```text
market_price
```

Required exact compatibility:

- entity ID
- financial scope
- quote currency / base monetary unit
- valuation `as_of`

All other v0.6 decisions must remain unchanged.

## Apply semantics / 적용 의미론

M17 approval/apply is extended additively for top-level `market_price`.

The applied diff records:

```text
before
after
source_market_price_package_sha256
source_snapshot_sha256
review_assertion_sha256
trading_date
observed_at
venue
quote_type
```

The source Draft remains unchanged and the result remains noncanonical.

## Interfaces / 인터페이스

CLI:

```text
market-price-candidate-build
market-price-candidate-validate
market-price-review-build
market-price-review-validate
market-price-finalize
market-price-validate
binding-build-with-market-price
binding-validate
```

Web:

```text
/market-price
/api/market-price/*
```

The Web surface is preparation/validation only. It exposes no direct Draft apply, file write, promotion, admission, or canonical-write route.
