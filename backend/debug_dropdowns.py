import duckdb
import os

def main():
    try:
        data_cache = "/Users/ardaerkan/codefest/patent-iq/data_cache"
        
        # 1. Industries
        print("\n--- INDUSTRIES ---")
        ind_path = os.path.join(data_cache, "portfolio_industry_distribution.parquet")
        if os.path.exists(ind_path):
            q = f"SELECT DISTINCT wipo_industry_code FROM '{ind_path}' ORDER BY wipo_industry_code"
            df = duckdb.query(q).df()
            for code in df['wipo_industry_code']:
                print(f"{{ code: \"{code}\", label: \"{code.replace('_', ' ').title()}\" }},")

        # 2. Countries
        print("\n--- COUNTRIES ---")
        master_path = os.path.join(data_cache, "portfolio_master.parquet")
        if os.path.exists(master_path):
            q = f"SELECT DISTINCT person_ctry_code FROM '{master_path}' WHERE person_ctry_code IS NOT NULL ORDER BY person_ctry_code"
            df = duckdb.query(q).df()
            print(df['person_ctry_code'].tolist())

        # 3. CPCs (Top 50 most common to avoid overwhelming list)
        print("\n--- CPCs (Top 50) ---")
        cpc_path = os.path.join(data_cache, "portfolio_cpc_distribution.parquet")
        if os.path.exists(cpc_path):
            q = f"""
            SELECT cpc_subclass, COUNT(*) as count 
            FROM '{cpc_path}' 
            GROUP BY cpc_subclass 
            ORDER BY count DESC 
            LIMIT 50
            """
            df = duckdb.query(q).df()
            for code in df['cpc_subclass']:
                print(f"{{ code: \"{code}\", label: \"{code}\" }},")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
