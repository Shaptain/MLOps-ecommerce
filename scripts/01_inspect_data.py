import pandas as pd

RAW_PATH = "data/raw/online_retail.xlsx"

def inspect():
    df = pd.read_excel(RAW_PATH)

    print("=" * 60)
    print("SHAPE:", df.shape)
    print("=" * 60)
    print("\nCOLUMN NAMES AND TYPES:\n")
    print(df.dtypes)
    print("\n" + "=" * 60)
    print("MISSING VALUES PER COLUMN:\n")
    print(df.isnull().sum())
    print("\n" + "=" * 60)
    print("DUPLICATE ROWS:", df.duplicated().sum())
    print("\n" + "=" * 60)
    print("SAMPLE ROWS:\n")
    print(df.head(5))
    print("\n" + "=" * 60)
    print("BASIC STATS (numeric columns):\n")
    print(df.describe())

if __name__ == "__main__":
    inspect()