"""
BSA Engine — Credit Assessment / Creditworthiness Scoring

Derives lending-relevant metrics from the already-computed analysis figures and
produces a composite credit score (0–100), a risk band, the sub-scores that fed
into it, and human-readable positive / negative factors.

This module is intentionally pure: it takes plain numbers and dicts (no PDF /
parsing concerns) so it is easy to unit-test and to re-tune. All weights and
thresholds live in `config.settings` where practical.
"""

from __future__ import annotations

from statistics import mean, pstdev
from typing import Optional


# Weighting of each sub-score in the composite (must sum to 1.0)
SUB_SCORE_WEIGHTS = {
    "income_stability": 0.25,
    "savings_capacity": 0.25,
    "balance_health": 0.20,
    "obligation_burden": 0.20,
    "conduct": 0.10,
}

BAND_THRESHOLDS = [
    (80, "EXCELLENT"),
    (65, "GOOD"),
    (50, "FAIR"),
    (35, "WEAK"),
    (0,  "POOR"),
]


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _band(score: float) -> str:
    for threshold, name in BAND_THRESHOLDS:
        if score >= threshold:
            return name
    return "POOR"


def _safe_div(a: float, b: float) -> Optional[float]:
    if not b:
        return None
    return a / b


def assess_creditworthiness(
    *,
    monthly_credits: list[dict],
    monthly_debits: list[dict],
    avg_monthly_credit: float,
    avg_monthly_debit: float,
    avg_eod: Optional[float],
    eod_series: dict,
    salary: dict,
    emi: dict,
    obligation_indicators: dict,
    summary_bounces: dict,
    high_risk_flags: list[dict],
    min_balance_threshold: float,
    regular_monthly_income: Optional[float] = None,
    monthly_obligations: Optional[float] = None,
) -> dict:
    """
    Build the `credit_assessment` block. All inputs are already computed in
    pipeline.analysis so this stays dependency-free.
    """

    # ── Income & obligations ──────────────────────────────────────────────────
    # Income basis preference:
    #   1. detected recurring salary (most reliable),
    #   2. regular (recurring) monthly income from income categorisation,
    #   3. average monthly credit (includes one-off inflows — least reliable).
    if salary.get("identified") and salary.get("probable_amount"):
        monthly_income = salary["probable_amount"]
        income_basis = "detected_salary"
    elif regular_monthly_income:
        monthly_income = regular_monthly_income
        income_basis = "recurring_income"
    else:
        monthly_income = avg_monthly_credit or 0.0
        income_basis = "average_monthly_credit"

    monthly_emi = emi.get("probable_emi_amount") or 0.0
    # Prefer the lexicon-derived total of all fixed obligations (EMI + credit
    # card + insurance + rent + MFI + KCC + education). Fall back to the single
    # detected EMI cluster when expense categorisation is unavailable.
    monthly_obligations = round(
        monthly_obligations if monthly_obligations else monthly_emi, 2
    )

    foir = _safe_div(monthly_obligations, monthly_income)  # 0..1 (lower better)

    # ── Surplus & savings ──────────────────────────────────────────────────────
    net_monthly_surplus = round(avg_monthly_credit - avg_monthly_debit, 2)
    savings_rate = _safe_div(net_monthly_surplus, avg_monthly_credit)  # can be <0

    inflow_outflow_ratio = _safe_div(avg_monthly_credit, avg_monthly_debit)

    # ── Income stability (coefficient of variation of monthly credits) ─────────
    credit_amounts = [m["amount"] for m in monthly_credits if m.get("amount")]
    income_cv = None
    if len(credit_amounts) >= 2 and mean(credit_amounts):
        income_cv = pstdev(credit_amounts) / mean(credit_amounts)

    # ── Balance health ─────────────────────────────────────────────────────────
    eod_values = list(eod_series.values()) if eod_series else []
    balance_cv = None
    if len(eod_values) >= 2 and mean(eod_values):
        balance_cv = pstdev(eod_values) / abs(mean(eod_values))
    negative_balance_days = sum(1 for v in eod_values if v < 0)

    # ── Conduct (bounces / risk flags) ─────────────────────────────────────────
    total_bounces = (
        (summary_bounces.get("inward") or 0)
        + (summary_bounces.get("outward") or 0)
        + (summary_bounces.get("emi") or 0)
    )
    high_sev_flags = sum(1 for f in high_risk_flags if f.get("severity") == "HIGH")
    med_sev_flags = sum(1 for f in high_risk_flags if f.get("severity") == "MEDIUM")

    # ── Sub-scores (0–100) ──────────────────────────────────────────────────────
    # 1. Income stability: CV of 0 → 100, CV of 0.6+ → 0
    if income_cv is None:
        income_stability_score = 50.0  # unknown / single month
    else:
        income_stability_score = _clamp(100 - (income_cv / 0.6) * 100)

    # 2. Savings capacity: savings rate 0 → 40, 0.3+ → 100, negative → 0
    if savings_rate is None:
        savings_capacity_score = 40.0
    else:
        savings_capacity_score = _clamp(40 + (savings_rate / 0.30) * 60)

    # 3. Balance health: avg balance vs MAB, penalise volatility & negative days
    if avg_eod is None:
        balance_health_score = 40.0
    else:
        ratio = _safe_div(avg_eod, min_balance_threshold) or 0.0
        balance_health_score = _clamp(40 + (ratio - 1) * 30)  # at MAB → 40, 3x MAB → 100
        if balance_cv:
            balance_health_score -= min(20.0, balance_cv * 20)
        balance_health_score -= min(30.0, negative_balance_days * 3)
        balance_health_score = _clamp(balance_health_score)

    # 4. Obligation burden: FOIR 0 → 100, 0.50 (RBI comfort ceiling) → 50, 1.0 → 0
    if foir is None:
        obligation_burden_score = 80.0  # no detected obligations
    else:
        obligation_burden_score = _clamp(100 - foir * 100)

    # 5. Conduct: start at 100, subtract penalties
    conduct_score = 100.0
    conduct_score -= total_bounces * 12
    conduct_score -= high_sev_flags * 20
    conduct_score -= med_sev_flags * 8
    conduct_score = _clamp(conduct_score)

    sub_scores = {
        "income_stability": round(income_stability_score, 1),
        "savings_capacity": round(savings_capacity_score, 1),
        "balance_health": round(balance_health_score, 1),
        "obligation_burden": round(obligation_burden_score, 1),
        "conduct": round(conduct_score, 1),
    }

    composite = sum(sub_scores[k] * w for k, w in SUB_SCORE_WEIGHTS.items())
    credit_score = int(round(_clamp(composite)))
    risk_band = _band(credit_score)

    # ── Factors (explainability) ────────────────────────────────────────────────
    positive, negative = _build_factors(
        salary=salary,
        monthly_income=monthly_income,
        net_monthly_surplus=net_monthly_surplus,
        savings_rate=savings_rate,
        foir=foir,
        income_cv=income_cv,
        avg_eod=avg_eod,
        min_balance_threshold=min_balance_threshold,
        negative_balance_days=negative_balance_days,
        total_bounces=total_bounces,
        high_risk_flags=high_risk_flags,
        inflow_outflow_ratio=inflow_outflow_ratio,
    )

    recommendation = _recommendation(credit_score, foir, total_bounces, high_sev_flags)

    return {
        "credit_score": credit_score,
        "risk_band": risk_band,
        "recommendation": recommendation,
        "monthly_income_estimate": round(monthly_income, 2),
        "income_basis": income_basis,
        "monthly_obligations_estimate": monthly_obligations,
        "foir": round(foir, 4) if foir is not None else None,
        "net_monthly_surplus": net_monthly_surplus,
        "savings_rate": round(savings_rate, 4) if savings_rate is not None else None,
        "inflow_outflow_ratio": round(inflow_outflow_ratio, 4) if inflow_outflow_ratio is not None else None,
        "income_volatility": round(income_cv, 4) if income_cv is not None else None,
        "balance_volatility": round(balance_cv, 4) if balance_cv is not None else None,
        "negative_balance_days": negative_balance_days,
        "average_bank_balance": round(avg_eod, 2) if avg_eod is not None else None,
        "sub_scores": sub_scores,
        "sub_score_weights": SUB_SCORE_WEIGHTS,
        "positive_factors": positive,
        "negative_factors": negative,
    }


def _build_factors(**ctx) -> tuple[list[str], list[str]]:
    positive: list[str] = []
    negative: list[str] = []

    if ctx["salary"].get("identified"):
        positive.append(
            f"Regular salary credit identified (~₹{ctx['monthly_income']:,.0f}/mo)"
        )
    else:
        negative.append("No regular salary pattern identified — income inferred from total credits")

    sr = ctx["savings_rate"]
    if sr is not None:
        if sr >= 0.20:
            positive.append(f"Healthy savings rate of {sr*100:.0f}% of inflows")
        elif sr < 0:
            negative.append("Spends more than it earns on average (negative monthly surplus)")
        elif sr < 0.05:
            negative.append(f"Thin savings buffer ({sr*100:.0f}% of inflows)")

    foir = ctx["foir"]
    if foir is not None:
        if foir <= 0.40:
            positive.append(f"Comfortable obligation burden (FOIR {foir*100:.0f}%)")
        elif foir > 0.55:
            negative.append(f"High obligation burden (FOIR {foir*100:.0f}% — above prudent ceiling)")

    cv = ctx["income_cv"]
    if cv is not None:
        if cv <= 0.15:
            positive.append("Very stable month-to-month income")
        elif cv > 0.45:
            negative.append("Volatile / irregular income across months")

    avg_eod = ctx["avg_eod"]
    mab = ctx["min_balance_threshold"]
    if avg_eod is not None:
        if avg_eod >= 2 * mab:
            positive.append(f"Strong average balance (₹{avg_eod:,.0f})")
        elif avg_eod < mab:
            negative.append(f"Average balance below MAB threshold (₹{avg_eod:,.0f} < ₹{mab:,.0f})")

    if ctx["negative_balance_days"] > 0:
        negative.append(f"Account went negative on {ctx['negative_balance_days']} day(s)")

    if ctx["total_bounces"] > 0:
        negative.append(f"{ctx['total_bounces']} cheque/EMI bounce event(s) — repayment-discipline risk")

    for f in ctx["high_risk_flags"]:
        if f.get("severity") == "HIGH":
            negative.append(f.get("detail", f.get("flag", "High-severity risk flag")))

    ratio = ctx["inflow_outflow_ratio"]
    if ratio is not None and ratio >= 1.1:
        positive.append(f"Inflows exceed outflows (ratio {ratio:.2f})")

    return positive, negative


def _recommendation(score: int, foir: Optional[float], bounces: int, high_sev: int) -> str:
    """Advisory only — final lending decision rests with the underwriter."""
    if high_sev > 0 or (foir is not None and foir > 0.65) or bounces >= 3:
        return "DECLINE / MANUAL_REVIEW — material risk indicators present"
    if score >= 65:
        return "LIKELY_APPROVE — strong cash-flow and conduct profile"
    if score >= 50:
        return "REVIEW — acceptable but verify income / obligations before approval"
    return "DECLINE / MANUAL_REVIEW — weak repayment-capacity signals"
