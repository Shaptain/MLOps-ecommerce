-- Dimension: Customer
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id     INTEGER PRIMARY KEY,
    country         VARCHAR(100)
);

-- Dimension: Product
CREATE TABLE IF NOT EXISTS dim_product (
    stock_code      VARCHAR(50) PRIMARY KEY,
    description     TEXT
);

-- Dimension: Date
CREATE TABLE IF NOT EXISTS dim_date (
    date_id         DATE PRIMARY KEY,
    day             INTEGER,
    month           INTEGER,
    year            INTEGER,
    day_of_week     VARCHAR(20)
);

-- Fact: Sales
CREATE TABLE IF NOT EXISTS fact_sales (
    invoice_no      VARCHAR(20),
    stock_code      VARCHAR(50) REFERENCES dim_product(stock_code),
    customer_id     INTEGER REFERENCES dim_customer(customer_id),
    invoice_date    DATE REFERENCES dim_date(date_id),
    quantity        INTEGER,
    unit_price      NUMERIC(10, 2),
    revenue         NUMERIC(12, 2),
    PRIMARY KEY (invoice_no, stock_code)
);