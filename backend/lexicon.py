"""
BSA Engine — Master Narration Lexicon (ported from Master-Narration-Lexicon v5)

A single source of truth for Indian bank-statement narration vocabulary across
five layers: Income, Obligation, Channel, Return, Forensic/AML. Each entry pairs
a canonical category with a case-insensitive regex tuned for private, PSU
(Finacle/BaNCS) and cooperative/regional formats and the NPCI rails
(UPI/IMPS/NEFT/RTGS/NACH/ECS).

Engine precedence when several categories match one line:
    return  >  forensic  >  obligation  >  income  >  channel
Behavioural ("B") categories require quantitative context and are NOT fired by
words alone — they are exposed here only for reference/labelling.
"""

from __future__ import annotations

import re
from typing import Optional


# ── Lexicon entries ─────────────────────────────────────────────────────────
# (type, key, label, mode, regex)
_RAW: list[tuple[str, str, str, str, str]] = [
    # ── Income & Inflows ────────────────────────────────────────────────────
    ("income", "salary", "Salary / Wages", "L",
     r"\b(salary|sal cr|salary credit|monthly sal|payroll|wages|stipend|remuneration|emp sal|staff sal|net pay|arrears of pay)\b|\bsal\b"),
    ("income", "business", "Business Receipts", "L",
     r"(razorpay|payu|ccavenue|billdesk|instamojo|cashfree|easebuzz|merchant settlement|pos settlement|settlement|against (bill|invoice)|inv-?\d|sales proceeds|collection)"),
    ("income", "rent", "Rent Income", "L",
     r"(rent received|rent cr|rental income|lease rent|rent from)"),
    ("income", "interest", "Interest / Dividend", "L",
     r"(int\.?\s*cr|int\.?coll|interest credit|interest pd|int pd|int paid|sb int|fd int|savings interest|credit interest|interest on|dividend on shares|share dividend|dividend|\bdiv\b|idcw)"),
    ("income", "forex_inward", "Foreign Inward Remittance", "L",
     r"(inward remit|inward remittance|foreign inward|\bfirc\b|\bswift\b|\bfcy\b|\bfcnr\b|remittance from|telegraphic transfer|\btt cr\b|wire transfer|paypal|payoneer|\bwise\b|western union|moneygram|\beefc\b|usd|gbp|eur|aed|sgd)"),
    ("income", "govt", "Govt Benefit / Pension", "L",
     r"(\bdbt\b|\bpfms\b|subsidy|pahal|\bnrega\b|pm kisan|pmkisan|scholarship|pension|\bppo\b|dbtl|aadhaar (dbt|credit))"),
    ("income", "maturity", "Investment Maturity / Redemption", "L",
     r"(fd maturity|rd maturity|mf redemption|redemption|maturity proceeds|\bcams\b|kfintech|karvy|surrender value|claim settlement|lic maturity|policy maturity|broker(age)? payout)"),
    ("income", "tax_refund", "Tax Refund", "L",
     r"(income tax refund|itr refund|\bit refund\b|cbdt refund|gst refund|tin[- ]nsdl|tax refund)"),
    ("income", "refund_rev", "Refunds & Reversals", "L",
     r"(refund|reversal|reversed|rev txn|txn reversal|auto reversal|failed (txn|transaction)|chargeback|charge back|cashback|cash back|merchant refund|imps return|neft return|refund of)"),
    ("income", "capital", "Capital Infusion / Own Funds", "L",
     r"(capital (introduced|infusion|contribution)|own contribution|proprietor.?s? fund|partner.?s? capital|equity infusion|owner fund|promoter (contribution|fund)|margin money)"),
    ("income", "agri", "Agricultural / Farm Income", "L",
     r"(mandi|\bapmc\b|krishi|crop (sale|proceeds)|agri(culture)? income|\bkcc\b|kisan credit|grain sale|produce sale|fasal|farm income|sugarcane|procurement)"),
    ("income", "pigmy", "Pigmy / Daily Deposit Collection", "L",
     r"(pigmy|pygmy|daily (deposit|collection)|agent (collection|deposit)|thrift deposit|daily dep|dd coll)"),

    # ── Obligations & Outflows ──────────────────────────────────────────────
    ("obligation", "emi", "EMI / Loan Repayment", "L",
     r"(\bemi\b|loan emi|loan instal|instalment|repayment|recovery|foreclosure|housing loan|home loan|auto loan|car loan|two wheeler loan|personal loan|\blap\b|gold loan|nach dr|ach[ _-]?d|ach dr|\becs\b|standing instr|\bmandate\b)|\b(bajaj fin|finserv|\bhdb\b|tata cap|fullerton|chola|shriram|muthoot|man+apuram|aditya birla fin|l&t fin)\b"),
    ("obligation", "cc", "Credit Card Payment", "L",
     r"(credit card|\bcc payment\b|card payment|\bcc bill\b|autopay cc|\bcred\b|cc-|amex|cc autopay)"),
    ("obligation", "insurance", "Insurance Premium", "L",
     r"(insurance|premium|\blic\b|hdfc life|icici pru|sbi life|max life|bajaj allianz|term plan|mediclaim|health insurance|policy prem|renewal premium)"),
    ("obligation", "invest", "Investment / Savings Outflow", "L",
     r"(\bsip\b|mutual fund|\bmf\b|groww|zerodha|upstox|\bcoin\b|kuvera|smallcase|\brd\b|recurring dep|\bppf\b|\bnps\b|elss|sweep|demat|\bnse\b|\bbse\b|\biccl\b|nsccl|indian clearing)"),
    ("obligation", "rent_paid", "Rent Paid", "L",
     r"(rent paid|house rent|office rent|\brent\b|to landlord|lease payment)"),
    ("obligation", "utility", "Utilities & Bills", "L",
     r"(electricity|bescom|mseb|\bbses\b|torrent power|tata power|water bill|gas bill|piped gas|broadband|postpaid|\bdth\b|\bbbps\b|bharat billpay|bill payment|recharge|fastag|toll|\bjio\b|airtel|\bvi \b|bsnl)"),
    ("obligation", "tax", "Tax & Statutory", "L",
     r"(\bgst\b|gstn|cgst|sgst|igst|\btds\b|\btcs\b|advance tax|self assessment|income tax|cbdt|itns|challan|prof(essional)? tax|\bepf\b|\besic\b|\bpf \b)"),
    ("obligation", "disbursal", "Loan Disbursal Inflow", "L",
     r"(loan disbursal|disbursement|\bdisb\b|loan cr|advance credit|payday|instant loan|loan disb)|\b(navi|cashe|kreditbee|moneyview|moneytap|paysense|lazypay|simpl|slice|zestmoney|\bfibe\b|earlysalary|early salary|mpokket|\bdmi\b|incred|home credit)\b"),
    ("obligation", "education", "Education / School Fees", "L",
     r"(school fee|college fee|tuition fee|tuition|education fee|exam fee|semester fee|hostel fee|coaching fee|university fee|academy fee|admission fee)"),
    ("obligation", "subscription", "Subscriptions / OTT / SaaS", "L",
     r"(netflix|amazon prime|prime video|hotstar|disney\+?|spotify|youtube premium|subscription|google one|icloud|adobe|microsoft 365|office 365|sonyliv|zee5|jiocinema|gym member|membership)"),
    ("obligation", "od", "Overdraft / CC Utilisation", "L",
     r"(overdraft|\bod a\/c\b|od drawdown|cash credit|\bcc a\/c\b|drawing power|\bdp \b|od int|overlimit|sanctioned limit|od util|temp od)"),
    ("obligation", "payroll", "Salary / Payroll Disbursed", "L",
     r"(salary (paid|disb|payout)|payroll (run|disb|upload)|staff salary|wages paid|salary to (employees|staff)|bulk salary|salary batch|salary upload)"),
    ("obligation", "supplier", "Supplier / Vendor / Purchase", "L",
     r"(vendor payment|supplier payment|purchase payment|to supplier|payment to vendor|raw material|\bpurchase\b|towards purchase|goods payment|trade payable)"),
    ("obligation", "mfi", "MFI / JLG / SHG Repayment", "L",
     r"(\bjlg\b|\bshg\b|micro ?finance|\bmfi\b|group loan|joint liability|self help group|weekly collection|fortnightly collection|centre meeting|bandhan|spandana|creditaccess|grameen|satin|muthoot microfin|fusion micro|asirvad|svatantra|annapurna)"),
    ("obligation", "kcc", "KCC / Crop Loan", "L",
     r"(\bkcc\b|kisan credit|crop loan|agri (loan|cc|advance)|kisan card|\bkgc\b|\bgcc\b|tractor loan|farm loan)"),
    ("obligation", "coop_share", "Cooperative Share Capital / Membership", "L",
     r"(share capital|shares allotment|member(ship)? fee|entrance fee|nominal member|dividend on shares|share dividend|co[- ]?op member|society share)"),

    # ── Channels & Instruments ──────────────────────────────────────────────
    ("channel", "atm", "ATM Withdrawal", "L",
     r"\b(atm|atw|nwd|owd|eaw|ats|nfs|awb|nwb|vat|mat|cash wdl|cash withdrawal|atm wdl|atm cash|self wdl|cwdr)\b"),
    ("channel", "cash", "Cash Deposit", "L",
     r"\b(cash dep|cash deposit|cdm|csh dep|by cash|cash receipt|\bbna\b|self cash dep)\b|\bcash\b"),
    ("channel", "cheque", "Cheque / Clearing", "L",
     r"\b(chq|cheque|chq dep|chq paid|\bcts\b|\bclg\b|clearing|micr clg|inward clg|outward clg|by clg|to clg|brn-clg)\b"),
    ("channel", "upi", "UPI / Wallet", "L",
     r"(\bupi\b|upi/p2a|upi/p2p|\bbhim\b|\bgpay\b|google pay|phonepe|paytm|amazonpay|amazon pay|mobikwik|freecharge|wallet)|@[a-z]+"),
    ("channel", "pos", "POS / Card Spend", "L",
     r"\b(pos|ecom|vps|rupay|visa|master|mastercard|merchant|swipe|card pos)\b"),
    ("channel", "transfer", "Transfers (NEFT/RTGS/IMPS)", "L",
     r"\b(neft|rtgs|imps|\btpt\b|to transfer|by transfer|xfer|\btrf\b|funds transfer|\bft\b|fund transfer|internal transfer|to clg|by clg|mmt|\bmob\b)\b|(bil\/|cms\/|ifn\/|mfn\/|inf\/|mbk\/|tps\/|brn\/|alk\/)"),
    ("channel", "mandate", "NACH / ECS Mandate / SI", "L",
     r"(\bnach\b|\bach\b|\becs\b|e-?mandate|\bmandate\b|standing instruction|\bsi-|auto ?debit|auto ?pay|si reg|mandate reg)"),
    ("channel", "dd_sweep", "DD / Pay Order / Sweep", "L",
     r"(demand draft|\bdd \b|pay order|\bpo issue\b|banker.?s cheque|\bbc issue\b|auto sweep|sweep[- ]?in|sweep[- ]?out|\bmod\b|flexi deposit)"),
    ("channel", "aeps", "AEPS / BC / Micro-ATM", "L",
     r"(\baeps\b|aadhaar enabled|micro[- ]?atm|business correspondent|bank mitra|aadhaar pay|\bbc txn\b)"),
    ("channel", "society", "Society / PACS / Sangha Linkage", "L",
     r"(\bpacs\b|primary agri|credit society|co[- ]?op(erative)? society|sangha|sangam|\bnidhi\b|souharda|seva sahakari|patpedhi|urban co[- ]?op|mahila (society|bank))"),

    # ── Returns, Bounces & Charges ──────────────────────────────────────────
    ("return", "ret_outward", "Outward Return / Dishonour", "L",
     r"(return(ed)?|\brtn\b|\bret\b|bounce|dishonou?r|\bnsf\b|funds insufficient|insufficient (funds|balance)|ecs rtn|nach rtn|ach[ _-]?rtn|chq rtn|cheque return|mandate fail|auto debit fail|emi bounce|non[ -]?payment|return memo|exceeds arrangement|refer to drawer|stop payment|payment stopped|account closed|signature (differs|mismatch)|stale|post[ -]?dated|effects not cleared)"),
    ("return", "ret_inward", "Inward Return", "L",
     r"(i\/w (ret|return)|inward (clg )?return|chq dep return|deposited cheque return|return of deposited|cheque returned unpaid|return inward|inw return)"),
    ("return", "charges", "Bank Charges / Penalty", "L",
     r"(charge|\bchrg\b|\bchg\b|chg:|\bchrgs\b|\bfee\b|min bal|amb chg|non maint|\bnmc\b|penal|penalty|sms chg|annual chg|\bamc\b|ledger folio|folio chg|inspection chg|incidental chg|service chg|return charge|rtn chg|cheque return charge|gst on chg|debit card chg|od int|overlimit)"),

    # ── Forensic & AML Signals ──────────────────────────────────────────────
    ("forensic", "structuring", "Cash Structuring / Smurfing", "B",
     r"\b(cash dep|cash deposit|cdm|by cash)\b"),
    ("forensic", "mule", "Pass-through / Money-Mule", "B",
     r"(neft|imps|rtgs|upi)"),
    ("forensic", "circular", "Circular / Round-Tripping", "B",
     r"(reversal|return of fund|temp(orary)? (credit|fund)|against earlier|adjustment|\badj\b|refund of advance)"),
    ("forensic", "window", "Window Dressing", "B",
     r"(temporary deposit|fund support|loan from friend|gift|hand loan|temp deposit)"),
    ("forensic", "forex_outward", "Foreign Outward / LRS", "L",
     r"(outward remit|outward remittance|foreign outward|\blrs\b|swift out|\btt dr\b|wire out|remittance to|fcy outward|a2 form|foreign travel|forex card load|intl txn|international txn)"),
    ("forensic", "gambling", "Gambling / Betting", "L",
     r"(dream11|dream 11|my11circle|my11|bet365|betway|1xbet|parimatch|\bstake\b|\brummy\b|pokerbaazi|junglee|teen patti|casino|lottery|gambl|betting|\bmpl\b|winzo|games24x7|\ba23\b|adda52|khelo)"),
    ("forensic", "crypto", "Crypto / VDA", "L",
     r"(wazirx|coindcx|coinswitch|zebpay|binance|kucoin|\bcrypto\b|bitcoin|\bbtc\b|ethereum|\busdt\b|\bvda\b|mudrex|giottus|unocoin|bitbns)"),
    ("forensic", "selftrf", "Self / Inter-Account Transfer", "L",
     r"(\bself\b|own account|own a\/c|inter[- ]?account|self transfer|to self|own transfer|between own|same customer)"),
    ("forensic", "suspense", "Suspense / Sundry / GL", "L",
     r"(suspense|sundry|general ledger|\bgl \b|office a\/c|\bmisc\b|unidentified|provisional|parking)"),
    ("forensic", "fakesal", "Fabricated Salary Routing", "B",
     r"\b(salary|sal cr|salary credit)\b"),
    ("forensic", "stacking", "EMI Stacking / Multi-Lender", "B",
     r"(\bemi\b|loan emi|nach dr|loan disbursal)|\b(navi|cashe|kreditbee|moneyview|paysense|lazypay|slice|zestmoney|fibe|mpokket|dmi|bajaj fin|hdb|tata cap)\b"),
    ("forensic", "source", "Gift / Source-of-Funds", "L",
     r"(gift|inheritance|legacy|estate|sale of property|sale proceeds|wedding gift|shagun|inherited|ancestral)"),
]

# Human-readable layer labels
TYPE_LABEL = {
    "income": "Income", "obligation": "Obligation", "channel": "Channel",
    "return": "Return", "forensic": "Forensic / AML",
}

# Engine precedence when several categories match one narration.
PRECEDENCE = {"return": 0, "forensic": 1, "obligation": 2, "income": 3, "channel": 4}


class _Entry:
    __slots__ = ("type", "key", "label", "mode", "regex")

    def __init__(self, t, k, lbl, m, rx):
        self.type = t
        self.key = k
        self.label = lbl
        self.mode = m
        self.regex = re.compile(rx, re.IGNORECASE)


LEXICON: list[_Entry] = [_Entry(*row) for row in _RAW]

# Fast lookups
BY_TYPE: dict[str, list[_Entry]] = {}
for _e in LEXICON:
    BY_TYPE.setdefault(_e.type, []).append(_e)


# ── Public API ──────────────────────────────────────────────────────────────

def classify(narration: str, types: Optional[set[str]] = None, lexical_only: bool = True) -> list[_Entry]:
    """All entries whose regex matches the narration, ordered by engine precedence."""
    if not narration:
        return []
    hits = []
    for e in LEXICON:
        if types and e.type not in types:
            continue
        if lexical_only and e.mode != "L":
            continue
        if e.regex.search(narration):
            hits.append(e)
    hits.sort(key=lambda e: PRECEDENCE.get(e.type, 9))
    return hits


_BY_KEY: dict[str, _Entry] = {e.key: e for e in LEXICON}

# Most-specific-first ordering so purpose categories win over the generic
# EMI/auto-debit catch-all (whose regex also matches bare NACH/ACH/ECS tokens).
_INCOME_ORDER = [
    "salary", "agri", "pigmy", "rent", "interest", "forex_inward", "govt",
    "maturity", "tax_refund", "capital", "business", "refund_rev",
]
_EXPENSE_ORDER = [
    "insurance", "cc", "invest", "mfi", "kcc", "education", "subscription",
    "rent_paid", "utility", "disbursal", "supplier", "coop_share", "tax",
    "od", "payroll", "emi",
]


def _first_ordered(narration: str, order: list[str]) -> Optional[_Entry]:
    if not narration:
        return None
    for key in order:
        e = _BY_KEY.get(key)
        if e and e.regex.search(narration):
            return e
    return None


def classify_income(narration: str) -> Optional[tuple[str, str]]:
    """Return (key, label) of the best income category for a credit, else None."""
    e = _first_ordered(narration, _INCOME_ORDER)
    return (e.key, e.label) if e else None


def classify_expense(narration: str) -> Optional[tuple[str, str]]:
    """Return (key, label) of the best obligation category for a debit, else None."""
    e = _first_ordered(narration, _EXPENSE_ORDER)
    return (e.key, e.label) if e else None


_CHANNEL_ORDER = ["atm", "cash", "cheque", "pos", "upi", "mandate",
                  "dd_sweep", "aeps", "society", "transfer"]


def detect_channel(narration: str) -> Optional[str]:
    """Return the channel/instrument key (atm, cash, upi, transfer, …)."""
    e = _first_ordered(narration, _CHANNEL_ORDER)
    return e.key if e else None


# Convenience keyword exports for legacy detectors (kept regex-backed here).
GAMBLING_REGEX = next(e.regex for e in LEXICON if e.key == "gambling")
CRYPTO_REGEX = next(e.regex for e in LEXICON if e.key == "crypto")
SELF_TRANSFER_REGEX = next(e.regex for e in LEXICON if e.key == "selftrf")
OUTWARD_RETURN_REGEX = next(e.regex for e in LEXICON if e.key == "ret_outward")
INWARD_RETURN_REGEX = next(e.regex for e in LEXICON if e.key == "ret_inward")
CHARGES_REGEX = next(e.regex for e in LEXICON if e.key == "charges")

# Obligation categories that represent genuine fixed/recurring commitments and
# should feed the FOIR / debt-burden calculation (excludes investments, taxes,
# supplier COGS, utilities, subscriptions which are not credit obligations).
FOIR_OBLIGATION_KEYS = {"emi", "cc", "insurance", "rent_paid", "mfi", "kcc", "education"}
