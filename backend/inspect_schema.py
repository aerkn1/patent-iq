import duckdb

try:
    conn = duckdb.connect("analytics.duckdb", read_only=True)
    print(conn.sql("DESCRIBE patent_core").df())
except Exception as e:
    print(e)
