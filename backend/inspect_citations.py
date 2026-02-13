
import duckdb
import sys
import os

# Add current directory to path so imports work
sys.path.append(os.getcwd())

from infrastructure.duckdb.parquet_registry import PARQUETS

def inspect(name):
    url = PARQUETS.get(name)
    if not url:
        print(f"Parquet {name} not found")
        return

    print(f"\n--- {name} ---")
    try:
        # Limit 1 to just get schema efficiently
        df = duckdb.query(f"SELECT * FROM '{url}' LIMIT 1").to_df()
        for col in df.columns:
            print(f"  {col}")
    except Exception as e:
        print(f"Error reading {name}: {e}")

if __name__ == "__main__":
    inspect("patent_citation_metrics")
    inspect("patent_citation_events_yearly")
    inspect("patent_core")
    inspect("ml_training_table")
    inspect("patent_citation_events_core")
    inspect("patent_portfolio_map")
