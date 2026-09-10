import pandas as pd
import os
import json
from datetime import datetime

SOURCE_FILE = "data/raw/online_retail.xlsx"
REJECTED_LOG = "data/logs/rejected_records.csv"
VALIDATION_SUMMARY = "data/logs/validation_summary.json"

def validate():
    df = pd.read_excel(SOURCE_FILE)
    original_count = len(df)

    issues = []

    # Rule 1: Invalid quantity (<= 0)
    invalid_qty = df[df["Quantity"] <= 0].copy()
    invalid_qty["reject_reason"] = "Invalid quantity (<= 0)"
    issues.append(invalid_qty)

    # Rule 2: Invalid price (<= 0)
    invalid_price = df[df["UnitPrice"] <= 0].copy()
    invalid_price["reject_reason"] = "Invalid unit price (<= 0)"
    issues.append(invalid_price)

    # Rule 3: Missing CustomerID
    missing_cust = df[df["CustomerID"].isnull()].copy()
    missing_cust["reject_reason"] = "Missing CustomerID"
    issues.append(missing_cust)

    # Rule 4: Cancelled invoices (InvoiceNo starts with 'C')
    cancelled = df[df["InvoiceNo"].astype(str).str.startswith("C")].copy()
    cancelled["reject_reason"] = "Cancelled invoice"
    issues.append(cancelled)

    # Rule 5: Duplicate rows
    duplicates = df[df.duplicated()].copy()
    duplicates["reject_reason"] = "Duplicate row"
    issues.append(duplicates)

    # Combine all rejected records (a row can appear more than once if it
    # fails multiple rules — that's fine, it's a log, not the cleaned data)
    rejected = pd.concat(issues, ignore_index=True)

    os.makedirs("data/logs", exist_ok=True)
    rejected.to_csv(REJECTED_LOG, index=False)

    summary = {
        "validation_timestamp": datetime.now().isoformat(),
        "total_records_checked": original_count,
        "invalid_quantity_count": len(invalid_qty),
        "invalid_price_count": len(invalid_price),
        "missing_customer_id_count": len(missing_cust),
        "cancelled_invoice_count": len(cancelled),
        "duplicate_row_count": len(duplicates),
        "total_rejected_rows_logged": len(rejected)
    }

    with open(VALIDATION_SUMMARY, "w") as f:
        json.dump(summary, f, indent=2)

    print("Validation complete.")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    return summary

if __name__ == "__main__":
    validate()