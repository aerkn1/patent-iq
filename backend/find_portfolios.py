
import duckdb
import sys
import os

sys.path.append(os.getcwd())
from infrastructure.duckdb.parquet_registry import PARQUETS
from infrastructure.caching import CacheManager

def list_portfolios():
    print("Ensuring cache...")
    local_parquets = CacheManager.ensure_cache(PARQUETS)
    conn = duckdb.connect()

    print("\n--- Portfolios ---")
    ppm_path = local_parquets["patent_portfolio_map"]
    query = f"""
    SELECT owner_id, COUNT(*) as count 
    FROM '{ppm_path}' 
    GROUP BY owner_id 
    ORDER BY count DESC 
    LIMIT 5
    """
    try:
        df = conn.execute(query).fetchdf()
        print(df.to_string())
    except Exception as e:
        print(f"Error querying portfolios: {e}")

if __name__ == "__main__":
    list_portfolios()
