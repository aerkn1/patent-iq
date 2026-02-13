import duckdb
from infrastructure.repositories.patent_citations_repo import PatentCitationsRepository

repo = PatentCitationsRepository()
try:
    print("Testing get_cumulative_timeseries for 482020668...")
    result = repo.get_cumulative_timeseries(482020668)
    print("Result:", result)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
