import pandas as pd
import os
import json
from datetime import datetime

SOURCE_FILE = "data/raw/online_retail.xlsx"
INGEST_LOG = "data/logs/ingestion_log.json"

def ingest():
    result = {
        "extraction_timestamp": datetime.now().isoformat(),
        "source_file": SOURCE_FILE,
        "source_type": "UCI Online Retail Dataset (local file)",
        "status": "FAILED",
        "row_count": None,
        "error": None
    }

    try:
        if not os.path.exists(SOURCE_FILE):
            raise FileNotFoundError(f"Source file not found: {SOURCE_FILE}")

        df = pd.read_excel(SOURCE_FILE)
        result["row_count"] = len(df)
        result["status"] = "SUCCESS"

        print(f"Ingestion successful. Rows ingested: {len(df)}")

    except Exception as e:
        result["error"] = str(e)
        print(f"Ingestion FAILED: {e}")

    # Append to log file (create if doesn't exist)
    os.makedirs("data/logs", exist_ok=True)
    logs = []
    if os.path.exists(INGEST_LOG):
        with open(INGEST_LOG, "r") as f:
            logs = json.load(f)
    logs.append(result)
    with open(INGEST_LOG, "w") as f:
        json.dump(logs, f, indent=2)

    return result["status"] == "SUCCESS"

if __name__ == "__main__":
    ingest()