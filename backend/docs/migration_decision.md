Backend Migration Status & Context
Date: 2025-01-25 Topic: Resolving Backend Latency / Database Migration

1. Recent Architecture Changes
We recently transitioned the backend storage layer to a "Serverless" architecture to avoid committing large binary files to Git::

Data Hosting: All .parquet files (Core, Rankings, Portfolios) were moved to Hugging Face Datasets (ardae1/analytics-parquets).
DuckDB Integration: The backend (
connection.py
) now uses the httpfs extension to read these files directly over HTTPS.
Lazy Loading: We switched from CREATE TABLE to CREATE OR REPLACE VIEW to fix startup timeouts. This defers data fetching until query time.
2. Current Situational Analysis (The Bottleneck)
Despite these optimizations, the backend is experiencing unacceptable latency (seconds to minutes) for standard API requests.

Technical Root Cause: "Columnar Shredding" over HTTP
Access Pattern: Our API performs high-frequency Point Lookups (e.g., "Get details for Patent ID 123").
Storage Format: Parquet is a Columnar format, optimized for large-scale scans (OLAP), not single-row retrieval (OLTP).
The Issue: Because the remote Parquet files are unsorted, DuckDB cannot use "Predicate Pushdown" to skip data. It is forced to download large chunks of every requested column (e.g., 100MB of IDs) just to find one record.
Bandwidth: A single page load can trigger hundreds of MBs of data transfer.
Verdict: The current "Parquet-over-HTTP" architecture is unsuitable for our transactional backend use case.

3. Migration Options (Decision Required)
We must migrate to a Row-Based Database (Postgres or SQLite) to achieve sub-millisecond lookups. Constraint: Our total dataset size is ~4 GB.

Option A: Managed Cloud PostgreSQL (Recommended for Team)
We deploy a shared Postgres instance in the cloud. All developers connect to it via DATABASE_URL.

Pros:
Single Source of Truth: All devs work on the exact same data.
Performance: Enterprise-grade speed and concurrency.
Zero Local Setup: New devs just add the .env var.
Cons:
Cost: exceeds free tiers (Supabase Free limit is 500MB). Requires ~ $15-25/month (e.g., Supabase Pro, Neon, or AWS RDS).
Implementation: sqlalchemy + psycopg.
Option B: Local SQLite / Local Postgres
We convert the 4GB data into a local database file (SQLite .db or Postgres dump) and distribute it.

Pros:
Free: No monthly cost.
Latency: Zero (local disk IO).
Cons:
Distribution Hell: Every developer must download a 4GB file manually.
Sync: "It works on my machine" issues if data versions diverge.
Disk Space: Bloats dev environments.
Option C: Self-Hosted Cloud Postgres
We rent a cheap VPS (e.g., Hetzner/DigitalOcean for $5/mo) and run Postgres on plain Docker.

Pros: Cheaper than Managed Cloud.
Cons: Maintenance burden (security updates, backups are manual).
Recommendation
If the budget permits $25/mo, Option A (Managed Cloud) is the standard professional choice. It allows the team to move fast without managing 4GB files locally.