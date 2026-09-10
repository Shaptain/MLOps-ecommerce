import pandas as pd
import os
import json
from datetime import datetime

SOURCE_FILE = "data/raw/online_retail.xlsx"
STAGING_FILE = "data/staging/online_retail_staged.csv"
CLEANED_FILE = "data/cleaned/online_retail_cleaned.csv"
TRANSFORM_LOG = "data/logs/transformation_log.json"

def transform():
    df = pd.read_excel(SOURCE_FILE)
    original_count = len(df)

    # --- STAGING: light standardization only, keep row count same ---
    df.columns = [c.strip() for c in df.columns]
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

    os.makedirs("data/staging", exist_ok=True)
    df.to_csv(STAGING_FILE, index=False)

    # --- CLEANING: apply the rules from Phase 3 ---
    step_counts = {"start": len(df)}

    # Remove cancelled invoices
    df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]
    step_counts["after_removing_cancelled"] = len(df)

    # Remove invalid quantity
    df = df[df["Quantity"] > 0]
    step_counts["after_removing_invalid_quantity"] = len(df)

    # Remove invalid price
    df = df[df["UnitPrice"] > 0]
    step_counts["after_removing_invalid_price"] = len(df)

    # Remove missing CustomerID (needed for customer-level analytics/mart)
    df = df[df["CustomerID"].notnull()]
    step_counts["after_removing_missing_customerid"] = len(df)
    df["CustomerID"] = df["CustomerID"].astype(int)

    # Remove duplicate rows
    df = df.drop_duplicates()
    step_counts["after_removing_duplicates"] = len(df)

    # Remove rows with unparseable dates
    df = df[df["InvoiceDate"].notnull()]
    step_counts["after_removing_invalid_dates"] = len(df)

    # --- Derived columns ---
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df["InvoiceDate"] = df["InvoiceDate"].dt.strftime("%Y-%m-%d %H:%M:%S")

    os.makedirs("data/cleaned", exist_ok=True)
    df.to_csv(CLEANED_FILE, index=False)

    log = {
        "transformation_timestamp": datetime.now().isoformat(),
        "original_row_count": original_count,
        "final_row_count": len(df),
        "rows_removed_total": original_count - len(df),
        "step_by_step_counts": step_counts
    }

    os.makedirs("data/logs", exist_ok=True)
    with open(TRANSFORM_LOG, "w") as f:
        json.dump(log, f, indent=2)

    print("Transformation complete.")
    print(json.dumps(log, indent=2))

    return log

if __name__ == "__main__":
    transform()