"""Dependency-free HTML/SVG visualization helpers / 의존성 없는 HTML·SVG 시각화 도우미.

Visualization consumes already-computed runtime results. It owns no valuation
formula and performs no canonical state mutation.

시각화는 이미 계산된 런타임 결과만 소비하며 가치평가 공식이나 정식상태 변경을
소유하지 않는다.
"""

from __future__ import annotations

import html
from math import isfinite
from typing import Any


def _num(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise ValueError("visualization values must be finite numbers")
    return float(value)


def _fmt(value: float, currency: str | None) -> str:
    if currency == "KRW":
        return f"₩{value:,.0f}"
    if currency == "USD":
        return f"${value:,.4f}" if abs(value) < 100 else f"${value:,.2f}"
    return f"{value:,.2f}"


def horizontal_value_chart(items: list[tuple[str, float]], *, currency: str | None = None, title: str = "") -> str:
    """Accessible horizontal SVG bar chart / 접근 가능한 가로 막대 SVG."""
    if not items:
        raise ValueError("chart items cannot be empty")
    clean = [(str(label), _num(value)) for label, value in items]
    if any(value < 0 for _, value in clean):
        raise ValueError("horizontal value chart requires non-negative values")
    maximum = max(value for _, value in clean) or 1.0
    width, left, right, row_h = 760, 150, 125, 46
    plot_w = width - left - right
    height = 46 + row_h * len(clean)
    rows: list[str] = []
    for index, (label, value) in enumerate(clean):
        y = 34 + index * row_h
        bar_w = max(1.0, plot_w * value / maximum)
        rows.append(
            f'<text x="0" y="{y + 16}" class="svg-label">{html.escape(label)}</text>'
            f'<rect x="{left}" y="{y}" width="{bar_w:.2f}" height="22" rx="5" class="svg-bar" />'
            f'<text x="{left + bar_w + 8:.2f}" y="{y + 16}" class="svg-value">{html.escape(_fmt(value, currency))}</text>'
        )
    aria = html.escape(title or "Valuation comparison / 가치 비교")
    return (
        f'<svg class="viz" viewBox="0 0 {width} {height}" role="img" aria-label="{aria}" '
        f'xmlns="http://www.w3.org/2000/svg">' + "".join(rows) + "</svg>"
    )


def equity_market_scenario_chart(runtime: dict[str, Any], market_price: float, currency: str | None) -> str:
    items = [("Market / 시장", _num(market_price))]
    for name in ("BEAR", "BASE", "BULL"):
        items.append((name.title(), _num(runtime[name]["value_per_share"])))
    return horizontal_value_chart(items, currency=currency, title="Market price vs intrinsic scenarios / 시장가격 vs 내재가치")


def fcff_trend_chart(runtime: dict[str, Any], *, currency: str | None = None) -> str:
    """Render three FCFF forecast polylines on a shared scale / 3대 FCFF 전망 추세."""
    names = ("BEAR", "BASE", "BULL")
    series = {name: [_num(v) for v in runtime[name]["forecast_fcff"]] for name in names}
    lengths = {len(values) for values in series.values()}
    if not lengths or len(lengths) != 1 or 0 in lengths:
        raise ValueError("FCFF series must have equal non-zero length")
    count = lengths.pop()
    all_values = [v for values in series.values() for v in values]
    low, high = min(all_values), max(all_values)
    span = high - low or 1.0
    width, height, left, top, bottom = 760, 260, 62, 24, 42
    plot_w, plot_h = width - left - 26, height - top - bottom
    colors = {"BEAR": "#f87171", "BASE": "#60a5fa", "BULL": "#34d399"}
    elements: list[str] = []
    for idx in range(count):
        x = left + (plot_w * idx / max(1, count - 1))
        elements.append(f'<text x="{x:.2f}" y="{height - 14}" text-anchor="middle" class="svg-axis">Y{idx + 1}</text>')
    for name in names:
        points: list[str] = []
        for idx, value in enumerate(series[name]):
            x = left + (plot_w * idx / max(1, count - 1))
            y = top + plot_h * (high - value) / span
            points.append(f"{x:.2f},{y:.2f}")
        elements.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{colors[name]}" stroke-width="3" />')
    legend = "".join(
        f'<span class="legend-item"><span class="legend-dot" style="background:{colors[name]}"></span>{name}</span>' for name in names
    )
    return (
        f'<div class="chart-wrap"><svg class="viz" viewBox="0 0 {width} {height}" role="img" aria-label="FCFF forecast trend / FCFF 전망 추세" xmlns="http://www.w3.org/2000/svg">'
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" class="svg-grid" />'
        + "".join(elements) + '</svg>'
        f'<div class="legend">{legend}</div><div class="muted small">Range / 범위: {_fmt(low, currency)} → {_fmt(high, currency)}</div></div>'
    )


def venture_outcome_chart(runtime: dict[str, Any], market_price: float, currency: str | None) -> str:
    items = [("Market / 시장", _num(market_price)), ("Expected / 기대가치", _num(runtime["expected_present_value_per_share"]))]
    for name, item in runtime["scenarios"].items():
        label = f"{name.title()} ({_num(item['probability']):.0%})"
        items.append((label, _num(item["present_value_per_share"])))
    return horizontal_value_chart(items, currency=currency, title="Venture probability outcomes / 벤처 확률 결과")


def evidence_classification_summary(counts: dict[str, int]) -> str:
    order = ("FACT", "NORMALIZED_FACT", "ASSUMPTION", "DERIVED", "INTERPRETATION", "UNKNOWN")
    cards = []
    for name in order:
        if name in counts:
            cards.append(f'<button type="button" class="filter-card" data-class="{html.escape(name)}"><strong>{int(counts[name])}</strong><span>{html.escape(name)}</span></button>')
    return '<div class="evidence-summary">' + "".join(cards) + '<button type="button" class="filter-card" data-class="ALL"><strong>↺</strong><span>ALL</span></button></div>'
