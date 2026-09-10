import os
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

MART_LOG = "data/logs/mart_build_log.json"


def get_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def ensure_mart_table_exists(engine):
    with open("sql/create_tables.sql", "r") as f:
        sql_script = f.read()
    with engine.begin() as conn:
        for statement in sql_script.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))


def build_customer_mart(engine):
    # "As of" date = the most recent invoice date in the whole dataset,
    # since our data is historical (not live), this stands in for "today"
    # when calculating recency.
    build_query = text("""
        WITH customer_agg AS (
            SELECT
                f.customer_id,
                dc.country,
                COUNT(DISTINCT f.invoice_no)     AS total_orders,
                SUM(f.quantity)                  AS total_quantity,
                SUM(f.revenue)                   AS total_revenue,
                MIN(f.invoice_date)               AS first_purchase_date,
                MAX(f.invoice_date)               AS last_purchase_date
            FROM fact_sales f
            JOIN dim_customer dc ON f.customer_id = dc.customer_id
            GROUP BY f.customer_id, dc.country
        ),
        max_date AS (
            SELECT MAX(invoice_date) AS ref_date FROM fact_sales
        )
        SELECT
            ca.customer_id,
            ca.country,
            ca.total_orders,
            ca.total_quantity,
            ca.total_revenue,
            ROUND(ca.total_revenue / ca.total_orders, 2) AS avg_order_value,
            ca.first_purchase_date,
            ca.last_purchase_date,
            (md.ref_date - ca.last_purchase_date)         AS recency_days,
            ca.total_orders                               AS frequency,
            ca.total_revenue                               AS monetary
        FROM customer_agg ca
        CROSS JOIN max_date md
    """)

    with engine.begin() as conn:
        rows = conn.execute(build_query).mappings().all()

        # Clear existing mart data before rebuilding (safe re-run)
        conn.execute(text("DELETE FROM customer_mart"))

        for row in rows:
            conn.execute(text("""
                INSERT INTO customer_mart
                    (customer_id, country, total_orders, total_quantity,
                     total_revenue, avg_order_value, first_purchase_date,
                     last_purchase_date, recency_days, frequency, monetary)
                VALUES
                    (:customer_id, :country, :total_orders, :total_quantity,
                     :total_revenue, :avg_order_value, :first_purchase_date,
                     :last_purchase_date, :recency_days, :frequency, :monetary)
            """), dict(row))

    return len(rows)


def main():
    engine = get_engine()
    ensure_mart_table_exists(engine)
    row_count = build_customer_mart(engine)

    log = {
        "build_timestamp": datetime.now().isoformat(),
        "customer_mart_rows": row_count
    }

    os.makedirs("data/logs", exist_ok=True)
    logs = []
    if os.path.exists(MART_LOG):
        with open(MART_LOG, "r") as f:
            logs = json.load(f)
    logs.append(log)
    with open(MART_LOG, "w") as f:
        json.dump(logs, f, indent=2)

    print("customer_mart built successfully.")
    print(json.dumps(log, indent=2))


if __name__ == "__main__":
    main()