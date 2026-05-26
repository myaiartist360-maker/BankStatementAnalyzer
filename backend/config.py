"""
BSA Engine — Central Configuration
All numeric thresholds and keyword lists are configurable via environment variables.
"""

from pydantic_settings import BaseSettings
from typing import FrozenSet


class Settings(BaseSettings):
    # ── API ───────────────────────────────────────────────────────────────────
    app_title: str = "BSA Engine"
    app_version: str = "1.0.0"
    backend_port: int = 8000
    results_dir: str = "results"

    # ── Balance Thresholds ────────────────────────────────────────────────────
    min_balance_threshold: float = 10_000.0        # ₹10,000 MAB
    balance_continuity_tolerance: float = 1.0      # ±₹1 rounding allowance

    # ── Analysis ──────────────────────────────────────────────────────────────
    outlier_std_multiplier: float = 5.0            # Transactions >5σ flagged
    round_trip_window_hours: int = 48
    round_trip_amount_tolerance: float = 0.02      # ±2%
    salary_amount_tolerance: float = 0.10          # ±10%
    salary_day_start: int = 1
    salary_day_end: int = 10
    salary_last_working_day_buffer: int = 5        # Last N days of month
    salary_min_months: int = 3                     # Months required to identify
    emi_amount_tolerance: float = 0.05             # ±5%
    emi_day_tolerance: int = 3                     # ±3 days
    high_value_cash_threshold: float = 50_000.0    # Flag ATM >₹50k/day
    gambling_high_severity_threshold: float = 50_000.0

    # ── Feature Flags ─────────────────────────────────────────────────────────
    enable_digital_signature_check: bool = False
    enable_ocr: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# ── Transaction Mode Patterns ─────────────────────────────────────────────────
# Order matters — first match wins
TRANSACTION_MODE_PATTERNS: list[tuple[str, list[str]]] = [
    ("UPI",      ["UPI", "UPI/", "/UPI", "UPIREF", "UPI-"]),
    ("NEFT",     ["NEFT", "NEFT-", "NEFT/"]),
    ("RTGS",     ["RTGS", "RTGS-", "RTGS/"]),
    ("IMPS",     ["IMPS", "IMPS/"]),
    ("CHEQUE",   ["CHQ", "CHEQUE", "CQ NO", "CHEQUE NO", "BY TRANSFER-CHEQUE"]),
    ("ATM",      ["ATM", "ATM-", "ATM WDL", "CASH WDL", "WITHDRAWAL"]),
    ("POS",      ["POS", "DEBIT CARD", "SWIPE", "MERCHANT"]),
    ("ECS",      ["ECS", "ECS DR", "ECS CR"]),
    ("NACH",     ["NACH", "NACH DR", "NACH CR", "MANDATE"]),
    ("SI",       ["SI ", "STANDING INSTRUCTION", "AUTO DEBIT", "AUTO-DEBIT"]),
    ("CASH",     ["CASH DEP", "CASH DEPOSIT", "CDM", "CASH WDL", "CASH PAYMENT"]),
    ("INTEREST", ["INTEREST", "INT CR", "INT CREDIT", "SAVINGS INTEREST"]),
    ("CHARGES",  ["CHARGES", "FEE", "PENALTY", "SERVICE CHARGE", "GST", "AMC"]),
]

# ── Reversal Patterns ──────────────────────────────────────────────────────────
REVERSAL_KEYWORDS: list[str] = [
    "REV", "REVERSAL", "RETURN", "BOUNCE", "DISHONOUR",
    "DISHONORED", "RETURNED", "CHQ RETURN", "CHEQUE RETURN"
]

# ── Gambling Keywords ─────────────────────────────────────────────────────────
GAMBLING_KEYWORDS: FrozenSet[str] = frozenset([
    "DREAM11", "MPL", "MY11CIRCLE", "FANTASY", "BETWAY", "1XBET",
    "PARIMATCH", "RUMMY", "POKER", "CASINO", "LOTTERY", "LOTTO",
    "PLAYRUMMY", "ADDA52", "JUNGLERUMMY", "POKERSTARS", "BETFAIR",
    "WINZO", "ZUPEE", "GAMES24X7", "SPORTA", "HOWZAT", "BALLEBAAZI"
])

# ── Crypto Keywords ───────────────────────────────────────────────────────────
CRYPTO_KEYWORDS: FrozenSet[str] = frozenset([
    "WAZIRX", "COINDCX", "ZEBPAY", "BITBNS", "BINANCE",
    "COINSWITCH", "BUYUCOIN"
])

# ── EMI / Bounce Patterns ─────────────────────────────────────────────────────
INWARD_BOUNCE_PATTERNS: list[str] = [
    "CHQ RETURN", "CHEQUE RETURN", "INWARD RETURN",
    "INSTRUMENT RETURN", "DISHONOURED", "DISHONORED"
]
OUTWARD_BOUNCE_PATTERNS: list[str] = ["OUTWARD RETURN"]
EMI_BOUNCE_PATTERNS: list[str] = [
    "NACH RETURN", "ECS RETURN", "SI FAILURE",
    "MANDATE RETURN", "AUTO DEBIT RETURN"
]

# ── High-Risk Narration Fragments ─────────────────────────────────────────────
ROUND_TRIP_NARRATIONS: list[str] = ["SELF TRANSFER", "IMPS", "NEFT"]

# ── Banks Known to Sign PDFs Digitally ───────────────────────────────────────
BANKS_WITH_DIGITAL_SIGNATURES: FrozenSet[str] = frozenset([
    "HDFC", "SBI", "ICICI", "AXIS", "KOTAK", "YES BANK"
])
