import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

CLEANED_FILE = "data/cleaned/online_retail_cleaned.csv"
LOAD_LOG = "data/logs/load_log.json"

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def load_dim_customer(df, engine):
    dim_customer = df[["CustomerID", "Country"]].drop_duplicates(subset=["CustomerID"])
    dim_customer = dim_customer.rename(columns={"CustomerID": "customer_id", "Country": "country"})

    with engine.begin() as conn:
        for _, row in dim_customer.iterrows():
            conn.execute(text("""
                INSERT INTO dim_customer (customer_id, country)
                VALUES (:customer_id, :country)
                ON CONFLICT (customer_id) DO NOTHING
            """), {"customer_id": int(row["customer_id"]), "country": row["country"]})

    return len(dim_customer)


def load_dim_product(df, engine):
    dim_product = df[["StockCode", "Description"]].drop_duplicates(subset=["StockCode"])
    dim_product = dim_product.rename(columns={"StockCode": "stock_code", "Description": "description"})

    with engine.begin() as conn:
        for _, row in dim_product.iterrows():
            conn.execute(text("""
                INSERT INTO dim_product (stock_code, description)
                VALUES (:stock_code, :description)
                ON CONFLICT (stock_code) DO NOTHING
            """), {"stock_code": row["stock_code"], "description": row["description"]})

    return len(dim_product)


def load_dim_date(df, engine):
    dates = pd.to_datetime(df["InvoiceDate"]).dt.date.unique()

    with engine.begin() as conn:
        for d in dates:
            conn.execute(text("""
                INSERT INTO dim_date (date_id, day, month, year, day_of_week)
                VALUES (:date_id, :day, :month, :year, :day_of_week)
                ON CONFLICT (date_id) DO NOTHING
            """), {
                "date_id": d,
                "day": d.day,
                "month": d.month,
                "year": d.year,
                "day_of_week": d.strftime("%A")
            })

    return len(dates)


def load_fact_sales(df, engine):
    fact = df[["InvoiceNo", "StockCode", "CustomerID", "InvoiceDate",
               "Quantity", "UnitPrice", "Revenue"]].copy()
    fact["InvoiceDate"] = pd.to_datetime(fact["InvoiceDate"]).dt.date
    fact = fact.rename(columns={
        "InvoiceNo": "invoice_no",
        "StockCode": "stock_code",
        "CustomerID": "customer_id",
        "InvoiceDate": "invoice_date",
        "Quantity": "quantity",
        "UnitPrice": "unit_price",
        "Revenue": "revenue"
    })

    # Fact table has composite PK (invoice_no, stock_code) — drop duplicates on that
    fact = fact.drop_duplicates(subset=["invoice_no", "stock_code"])

    inserted = 0
    with engine.begin() as conn:
        for _, row in fact.iterrows():
            result = conn.execute(text("""
                INSERT INTO fact_sales
                    (invoice_no, stock_code, customer_id, invoice_date, quantity, unit_price, revenue)
                VALUES
                    (:invoice_no, :stock_code, :customer_id, :invoice_date, :quantity, :unit_price, :revenue)
                ON CONFLICT (invoice_no, stock_code) DO NOTHING
            """), {
                "invoice_no": row["invoice_no"],
                "stock_code": row["stock_code"],
                "customer_id": int(row["customer_id"]),
                "invoice_date": row["invoice_date"],
                "quantity": int(row["quantity"]),
                "unit_price": float(row["unit_price"]),
                "revenue": float(row["revenue"])
            })
            inserted += result.rowcount

    return len(fact), inserted


def load_all():
    engine = get_engine()
    df = pd.read_csv(CLEANED_FILE)

    log = {"load_timestamp": datetime.now().isoformat()}

    print("Loading dim_customer...")
    log["dim_customer_rows"] = load_dim_customer(df, engine)

    print("Loading dim_product...")
    log["dim_product_rows"] = load_dim_product(df, engine)

    print("Loading dim_date...")
    log["dim_date_rows"] = load_dim_date(df, engine)

    print("Loading fact_sales...")
    total_candidates, actually_inserted = load_fact_sales(df, engine)
    log["fact_sales_candidate_rows"] = total_candidates
    log["fact_sales_newly_inserted"] = actually_inserted

    os.makedirs("data/logs", exist_ok=True)
    logs = []
    if os.path.exists(LOAD_LOG):
        with open(LOAD_LOG, "r") as f:
            logs = json.load(f)
    logs.append(log)
    with open(LOAD_LOG, "w") as f:
        json.dump(logs, f, indent=2)

    print("\nLoad complete.")
    print(json.dumps(log, indent=2))


if __name__ == "__main__":
    load_all()