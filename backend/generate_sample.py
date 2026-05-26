"""
BSA Engine — Synthetic Bank Statement Generator
Generates realistic dummy statements for testing.

Usage:
    python generate_sample.py [--months 6] [--with-gambling] [--with-bounces]

Outputs:
    samples/sample_statement_aa.json   — AA JSON format
    samples/sample_statement.csv       — CSV for manual inspection
"""

import json
import random
import argparse
from datetime import date, timedelta
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent / "samples"
SAMPLE_DIR.mkdir(exist_ok=True)

NARRATIONS = {
    "salary":   ["NEFT/SALARY/INFOSYS LTD/", "SALARY CREDIT NEFT/TATA CONSULTANCY/",
                 "IMPS/EMPLOYER CREDIT/WIPRO LTD/"],
    "grocery":  ["POS/DMART/RETAIL", "UPI/BIGBASKET/PURCHASE", "ZEPTO PAYMENTS PVT LTD"],
    "upi":      ["UPI/9876543210/PHONEPE", "UPI/PAY TO SWIGGY/GPAY", "UPI/AMAZON PAYMENTS/"],
    "emi":      ["NACH DR/HDFC HOME LOAN/EMI", "NACH DR/BAJAJ FINANCE/LOAN EMI",
                 "ECS DR/TATA CAPITAL/AUTO DEBIT"],
    "utility":  ["ELECTRICITY BILL/BESCOM/REF", "TATA SKY RECHARGE/", "AIRTEL POSTPAID/"],
    "atm":      ["ATM WDL/SBI ATM/MG ROAD", "CASH WITHDRAWAL/HDFC ATM/"],
    "gambling": ["UPI/DREAM11 FANTASY/PAY", "WINZO GAMES PRIVATE LIMITED/",
                 "ADDA52/RUMMY PAYMENTS/"],
    "crypto":   ["WAZIRX TECHNOLOGIES/CRYPTO", "COINDCX GO/PURCHASE"],
    "interest": ["SAVINGS INTEREST CREDIT", "INT CR ON SAVINGS ACCOUNT"],
    "charges":  ["SMS ALERT CHARGES", "ACCOUNT MAINTENANCE CHARGES/GST"],
    "inward_bounce": ["CHQ RETURN/INSTRUMENT RETURN/DR", "INWARD CHQ RETURN/DISHONOURED/"],
}


def generate_aa_json(months: int = 6, with_gambling: bool = False, with_bounces: bool = False) -> dict:
    start = date.today().replace(day=1) - timedelta(days=months * 30)
    end   = date.today()

    transactions = []
    balance = 85_000.0
    txn_date = start
    serial = 1

    while txn_date <= end:
        # Salary on 5th of each month
        if txn_date.day == 5:
            salary_amount = round(random.uniform(55_000, 65_000), 2)
            balance += salary_amount
            transactions.append(_txn(txn_date, "CREDIT", salary_amount, balance,
                                     random.choice(NARRATIONS["salary"]), "NEFT", serial))
            serial += 1

        # EMI on 10th
        if txn_date.day == 10:
            emi = round(random.uniform(12_000, 12_500), 2)
            balance -= emi
            transactions.append(_txn(txn_date, "DEBIT", emi, balance,
                                     random.choice(NARRATIONS["emi"]), "NACH", serial))
            serial += 1

        # Random daily transactions (1–4)
        for _ in range(random.randint(0, 3)):
            if random.random() < 0.6:  # 60% debit
                kind = random.choice(["grocery", "upi", "atm", "utility"])
                amt = round(random.uniform(100, 5_000), 2)
                balance -= amt
                balance = max(balance, 500)  # keep positive
                transactions.append(_txn(txn_date, "DEBIT", amt, balance,
                                         random.choice(NARRATIONS[kind]),
                                         _mode(kind), serial))
            else:  # credit
                amt = round(random.uniform(500, 10_000), 2)
                balance += amt
                transactions.append(_txn(txn_date, "CREDIT", amt, balance,
                                         "UPI/GPAY CREDIT/FRIEND", "UPI", serial))
            serial += 1

        # Interest on last day of month
        if (txn_date + timedelta(days=1)).day == 1 or txn_date == end:
            interest = round(balance * 0.003, 2)
            balance += interest
            transactions.append(_txn(txn_date, "CREDIT", interest, balance,
                                     NARRATIONS["interest"][0], "INTEREST", serial))
            serial += 1

        # Bank charges on 28th
        if txn_date.day == 28:
            charge = round(random.uniform(50, 200), 2)
            balance -= charge
            transactions.append(_txn(txn_date, "DEBIT", charge, balance,
                                     NARRATIONS["charges"][0], "CHARGES", serial))
            serial += 1

        # Gambling (optional)
        if with_gambling and random.random() < 0.08:
            amt = round(random.uniform(200, 5_000), 2)
            balance -= amt
            transactions.append(_txn(txn_date, "DEBIT", amt, balance,
                                     random.choice(NARRATIONS["gambling"]), "UPI", serial))
            serial += 1

        # Bounce (optional)
        if with_bounces and txn_date.day in (15, 25) and random.random() < 0.3:
            amt = round(random.uniform(1_000, 10_000), 2)
            transactions.append(_txn(txn_date, "DEBIT", amt, balance,
                                     random.choice(NARRATIONS["inward_bounce"]), "CHEQUE", serial))
            serial += 1

        txn_date += timedelta(days=1)

    payload = {
        "fipId": "HDFC0001234",
        "Summary": {
            "name": "RAJESH KUMAR SHARMA",
            "accNo": "XXXXXXXX9876",
            "ifscCode": "HDFC0001234",
            "bank": "HDFC Bank",
            "branch": "MG Road Bengaluru",
            "openingBalance": 85_000.0,
            "closingBalance": round(balance, 2),
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
        },
        "Transactions": {
            "Transaction": transactions,
        },
    }
    return payload


def _txn(d: date, typ: str, amount: float, balance: float,
         narration: str, mode: str, serial: int) -> dict:
    return {
        "transactionDate": d.isoformat(),
        "valueDate": d.isoformat(),
        "type": typ,
        "amount": round(amount, 2),
        "currentBalance": round(balance, 2),
        "narration": narration,
        "mode": mode,
        "txnId": f"TXN{serial:06d}",
    }


def _mode(kind: str) -> str:
    mapping = {
        "grocery": "POS", "upi": "UPI", "atm": "ATM",
        "utility": "NACH", "charges": "CHARGES"
    }
    return mapping.get(kind, "OTHER")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic bank statement")
    parser.add_argument("--months", type=int, default=6)
    parser.add_argument("--with-gambling", action="store_true")
    parser.add_argument("--with-bounces", action="store_true")
    args = parser.parse_args()

    aa = generate_aa_json(args.months, args.with_gambling, args.with_bounces)
    out = SAMPLE_DIR / "sample_statement_aa.json"
    out.write_text(json.dumps(aa, indent=2), encoding="utf-8")
    print(f"✅ Generated {len(aa['Transactions']['Transaction'])} transactions → {out}")

    # Also write a quick curl command
    import base64

    curl_file = SAMPLE_DIR / "test_curl.sh"
    curl_file.write_text(
        f"""#!/bin/bash
# Test the BSA engine with the generated AA JSON
curl -s -X POST http://localhost:8000/api/v1/analyse \\
  -H "Content-Type: application/json" \\
  -d @- << 'EOF'
{{"input_type": "account_aggregator_json", "aa_json": {json.dumps(aa)}}}
EOF
""",
        encoding="utf-8"
    )
    print(f"✅ curl test script → {curl_file}")
