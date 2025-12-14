# PatentIQ Database Tutorial

**Purpose:** Comprehensive guide to PATSTAT and INPADOC databases - what data is available, how to access it, and how PatentIQ uses it.

**Audience:** All developers, especially Data Lead

---

## Table of Contents

1. [Database Overview](#1-database-overview)
2. [PATSTAT Core Tables](#2-patstat-core-tables)
3. [PATSTAT Classification Tables](#3-patstat-classification-tables)
4. [PATSTAT Citation Tables](#4-patstat-citation-tables)
5. [PATSTAT Family Tables](#5-patstat-family-tables)
6. [INPADOC Legal Events](#6-inpadoc-legal-events)
7. [PatentIQ Data Requirements Map](#7-patentiq-data-requirements-map)
8. [Query Patterns & Examples](#8-query-patterns--examples)
9. [Performance Optimization](#9-performance-optimization)
10. [Data Quality & Validation](#10-data-quality--validation)

---

## 1. Database Overview

### 1.1 What is PATSTAT?

**PATSTAT** (Worldwide Patent Statistical Database) is the EPO's comprehensive database for patent statistics and analytics.

**Key Facts:**
- **Provider:** European Patent Office (EPO)
- **Coverage:** 100+ patent offices worldwide
- **Records:** 100+ million patent documents
- **Historical:** From 1880s to present
- **Update Frequency:** Twice yearly (Spring/Autumn editions)
- **Format:** PostgreSQL relational database
- **Size:** ~500GB compressed

**What PATSTAT Contains:**
- Bibliographic data (titles, inventors, assignees)
- Citation data (who cites whom)
- Classification data (technology categories)
- Family data (related applications worldwide)
- Legal status data (INPADOC integration)

**What PATSTAT Does NOT Contain:**
- Full patent text (abstracts only)
- Detailed claim text (claim count available separately)
- Real-time data (6-12 month lag)
- Some national office specific data

### 1.2 PatentIQ Database Environment

**Our Setup:**
- **Database:** PostgreSQL 14+
- **Access:** Python via `epo.tipdata.patstat` client
- **Environment:** PROD (production PATSTAT instance)
- **ORM:** SQLAlchemy 2.0+
- **Scope:** EPO granted patents, 2015-2024

**Connection Pattern:**
```python
from epo.tipdata.patstat import PatstatClient

# Initialize client
patstat = PatstatClient(env="PROD")

# Get database session
db = patstat.orm()

# Query example
from epo.tipdata.patstat.database.models import TLS211_PAT_PUBLN

result = db.query(TLS211_PAT_PUBLN).filter(
    TLS211_PAT_PUBLN.publn_auth == 'EP'
).first()
```

### 1.3 Database Schema Overview

**Table Naming Convention:**
- All tables prefixed with `TLS` (Table Library System)
- Three-digit number indicates functional area
- Example: `TLS211_PAT_PUBLN` = Table 211, Patent Publications

**Functional Areas:**
- **201-209:** Applications and persons
- **210-219:** Publications and families
- **220-229:** Classifications and technical fields
- **230-239:** Legal events (INPADOC)

**Key Identifier Types:**

| ID Type | Description | Example | Primary Use |
|---------|-------------|---------|-------------|
| `appln_id` | Application identifier (unique per application) | 123456789 | Joins across application-level tables |
| `pat_publn_id` | Publication identifier (unique per publication) | 987654321 | Joins across publication-level tables |
| `person_id` | Assignee/inventor identifier | 456789123 | Linking people to applications |
| `docdb_family_id` | Family identifier | 789123456 | Grouping related applications |

---

## 2. PATSTAT Core Tables

### 2.1 TLS201_APPLN (Patent Applications)

**Purpose:** Core table containing one row per patent application.

**Key Fields:**

| Field | Type | Description | PatentIQ Use |
|-------|------|-------------|--------------|
| `appln_id` | INTEGER | **Primary key** - unique application ID | Join key for all analysis |
| `appln_nr` | VARCHAR(20) | Application number (e.g., "20150001234") | Identification |
| `appln_auth` | CHAR(2) | Filing authority (e.g., "EP", "US") | Filter for EPO |
| `appln_filing_date` | DATE | Filing date | **Calculate age**, temporal filtering |
| `appln_filing_year` | INTEGER | Filing year | **Cohort analysis**, filtering |
| `appln_kind` | CHAR(2) | Application kind | Usually 'A' for applications |
| `granted` | CHAR(1) | Grant status (Y/N) | **Legal strength indicator** |
| `nb_applicants` | INTEGER | Number of applicants | Ownership complexity |
| `nb_inventors` | INTEGER | Number of inventors | Invention complexity |

**Typical Row:**
```
appln_id: 123456789
appln_nr: 20150001234
appln_auth: EP
appln_filing_date: 2015-03-15
appln_filing_year: 2015
granted: Y
nb_applicants: 1
nb_inventors: 3
```

**PatentIQ Query Pattern:**
```sql
SELECT 
    appln_id,
    appln_filing_date,
    appln_filing_year,
    granted,
    nb_applicants,
    nb_inventors
FROM tls201_appln
WHERE appln_auth = 'EP'
  AND appln_filing_year >= 2015
  AND granted = 'Y';
```

**Why This Table Matters:**
- **Central hub** for joining to other tables
- **Filing date** used to calculate patent age
- **Granted flag** filters for granted patents only
- **Filing year** used for cohort analysis and ML training sets

---

### 2.2 TLS211_PAT_PUBLN (Patent Publications)

**Purpose:** One row per patent publication (applications can have multiple publications).

**Key Fields:**

| Field | Type | Description | PatentIQ Use |
|-------|------|-------------|--------------|
| `pat_publn_id` | INTEGER | **Primary key** - unique publication ID | **Join key for citations** |
| `publn_auth` | CHAR(2) | Publishing authority (e.g., "EP") | Filter for EPO |
| `publn_nr` | VARCHAR(20) | Publication number | **User-facing patent number** |
| `publn_kind` | CHAR(4) | Publication kind (e.g., "B1", "A1") | **Filter for granted (B1/B2)** |
| `publn_date` | DATE | Publication date | Grant date for B1/B2 |
| `appln_id` | INTEGER | **Foreign key** to TLS201_APPLN | Join to application data |
| `publn_first_grant` | CHAR(1) | Is this first grant publication? (Y/N) | Identify initial grant |
| `publn_claims` | INTEGER | Number of claims | **Legal strength indicator** |

**Publication Kinds (Important):**
- **A1:** Application published (not granted)
- **A2:** Application without search report
- **B1:** First publication of grant
- **B2:** Grant after opposition amendments

**PatentIQ Focus:** We use **B1** and **B2** publications only (granted patents).

**Typical Row:**
```
pat_publn_id: 987654321
publn_auth: EP
publn_nr: 1234567
publn_kind: B1
publn_date: 2017-06-15
appln_id: 123456789
publn_first_grant: Y
publn_claims: 18
```

**Critical Join to Applications:**
```sql
SELECT 
    p.publn_nr,
    p.publn_kind,
    p.publn_date,
    a.appln_filing_date,
    EXTRACT(YEAR FROM AGE(p.publn_date, a.appln_filing_date)) as years_to_grant
FROM tls211_pat_publn p
JOIN tls201_appln a ON p.appln_id = a.appln_id
WHERE p.publn_auth = 'EP'
  AND p.publn_kind IN ('B1', 'B2')
  AND a.appln_filing_year >= 2015;
```

**Why This Table Matters:**
- **User-facing patent numbers** (EP1234567B1 comes from here)
- **Publication kind** filters for granted patents
- **Grant date** (publn_date for B1/B2) used to calculate time from filing to grant
- **Citation analysis** uses pat_publn_id as join key

---

### 2.3 TLS206_PERSON (Assignees and Inventors)

**Purpose:** Contains information about persons (companies and individuals) involved in patents.

**Key Fields:**

| Field | Type | Description | PatentIQ Use |
|-------|------|-------------|--------------|
| `person_id` | INTEGER | **Primary key** - unique person ID | Join key |
| `person_name` | VARCHAR(500) | Name (cleaned/harmonized) | **Company identification** |
| `person_name_orig_lg` | VARCHAR(500) | Original language name | Backup for search |
| `person_ctry_code` | CHAR(2) | Country code | Geographic analysis |
| `psn_sector` | VARCHAR(10) | Sector (e.g., "COMPANY", "INDIVIDUAL") | Filter for companies |
| `han_id` | INTEGER | Harmonized name ID (groups name variants) | **Company consolidation** |

**Person Types:**
- **COMPANY:** Corporate entities (our primary focus)
- **INDIVIDUAL:** Natural persons
- **GOV:** Government entities
- **UNIVERSITY:** Academic institutions

**Name Harmonization:**
- EPO attempts to harmonize name variants
- `han_id` groups together: "Siemens AG", "Siemens Aktiengesellschaft", "SIEMENS AG"
- Not perfect - manual verification may be needed

**Typical Rows:**
```
person_id: 11111
person_name: Siemens AG
person_ctry_code: DE
psn_sector: COMPANY
han_id: 55555

person_id: 11112
person_name: Siemens Aktiengesellschaft
person_ctry_code: DE
psn_sector: COMPANY
han_id: 55555  (same han_id!)
```

**PatentIQ Use Cases:**
- **Company search:** Find all name variants
- **Portfolio analysis:** Get all patents for an assignee
- **Licensing intelligence:** Identify active companies in technology spaces

---

### 2.4 TLS207_PERS_APPLN (Person-Application Link)

**Purpose:** Links persons (assignees/inventors) to applications.

**Key Fields:**

| Field | Type | Description | PatentIQ Use |
|-------|------|-------------|--------------|
| `person_id` | INTEGER | **Foreign key** to TLS206_PERSON | Who |
| `appln_id` | INTEGER | **Foreign key** to TLS201_APPLN | Which patent |
| `applt_seq_nr` | INTEGER | Applicant sequence number (0 if not applicant) | **Is this person an applicant?** |
| `invt_seq_nr` | INTEGER | Inventor sequence number (0 if not inventor) | **Is this person an inventor?** |

**Important Note:** Composite primary key is (`person_id`, `appln_id`, `applt_seq_nr`, `invt_seq_nr`).

**Role Identification:**
- `applt_seq_nr > 0` → Person is an **applicant** (assignee/owner)
- `invt_seq_nr > 0` → Person is an **inventor**
- Both can be > 0 (inventor-owned patents)

**Get Patents for a Company:**
```sql
SELECT 
    pers.person_name,
    p.publn_nr,
    a.appln_filing_year
FROM tls206_person pers
JOIN tls207_pers_appln link ON pers.person_id = link.person_id
JOIN tls201_appln a ON link.appln_id = a.appln_id
JOIN tls211_pat_publn p ON a.appln_id = p.appln_id
WHERE pers.person_name LIKE '%Siemens%'
  AND link.applt_seq_nr > 0  -- Applicant, not just inventor
  AND p.publn_kind IN ('B1', 'B2')
  AND a.appln_auth = 'EP';
```

**Why This Matters:**
- **Company portfolio extraction** for portfolio analysis (UC-02)
- **Licensing intelligence** - find active companies in technology
- **Competitive analysis** - who are the key players?

---

## 3. PATSTAT Classification Tables

### 3.1 TLS224_APPLN_CPC (CPC Classifications)

**Purpose:** Maps applications to Cooperative Patent Classification (CPC) codes.

**Key Fields:**

| Field | Type | Description | PatentIQ Use |
|-------|------|-------------|--------------|
| `appln_id` | INTEGER | **Foreign key** to application | Join key |
| `cpc_class_symbol` | VARCHAR(19) | Full CPC code (e.g., "A61B 5/00") | **Technology categorization** |
| `cpc_scheme` | VARCHAR(5) | CPC scheme version | Ensure consistency |
| `cpc_version` | VARCHAR(10) | CPC version date | Track changes |
| `cpc_position` | CHAR(1) | Position (F=first/main, L=later) | **Identify main CPC** |
| `cpc_gener_auth` | CHAR(2) | Authority generating code | Data source |

**CPC Code Structure:**
```
A61B 5/00
│││  │
│││  └──── Subgroup (2+ digits)
││└─────── Main group (1-4 digits)
│└──────── Subclass (1 letter)
└───────── Class (2 digits)
         Section (1 letter)

Full breakdown:
A        = Human Necessities
A61      = Medical or veterinary science
A61B     = Diagnosis; Surgery; Identification
A61B 5   = Detecting, measuring or recording
A61B 5/00 = For diagnostic purposes
```

**Multiple CPCs per Patent:**
- Patents typically have 5-15 CPC codes
- **Primary CPC** (cpc_position='F') is most important
- Additional CPCs provide context

**Typical Rows for One Patent:**
```
appln_id: 123456789, cpc_class_symbol: A61B 5/00, cpc_position: F  (main)
appln_id: 123456789, cpc_class_symbol: A61B 5/145, cpc_position: L
appln_id: 123456789, cpc_class_symbol: G01N 33/49, cpc_position: L
```

**Get CPC Codes for Patents:**
```sql
SELECT 
    p.publn_nr,
    cpc.cpc_class_symbol,
    cpc.cpc_position,
    SUBSTRING(cpc.cpc_class_symbol, 1, 1) as cpc_section,
    SUBSTRING(cpc.cpc_class_symbol, 1, 4) as cpc_subclass
FROM tls211_pat_publn p
JOIN tls201_appln a ON p.appln_id = a.appln_id
JOIN tls224_appln_cpc cpc ON a.appln_id = cpc.appln_id
WHERE p.publn_auth = 'EP'
  AND p.publn_kind IN ('B1', 'B2')
  AND p.publn_nr = '1234567';
```

**PatentIQ Use Cases:**
1. **Field normalization:** Compare citations within CPC section
2. **Technology trends:** Identify growing vs. declining CPC codes
3. **Market mapping:** Map CPC to industries (via WIPO concordance)
4. **Competitive landscape:** Find other companies in same CPC
5. **ML features:** One-hot encode CPC section (9 categories)

---

### 3.2 TLS209_APPLN_IPC (IPC Classifications)

**Purpose:** International Patent Classification (older system).

**When to Use:**
- Fallback if CPC not available (~2% of cases)
- International comparisons (non-EPO offices)

**Key Difference from CPC:**
- Less granular (70K categories vs. CPC's 250K)
- Still widely used globally
- Similar hierarchical structure

**PatentIQ Approach:**
- **Primary:** Use CPC (TLS224)
- **Fallback:** Use IPC if CPC missing

---

## 4. PATSTAT Citation Tables

### 4.1 TLS212_CITATION (Citation Relationships)

**Purpose:** Records which patents cite which other patents.

**Key Fields:**

| Field | Type | Description | PatentIQ Use |
|-------|------|-------------|--------------|
| `pat_publn_id` | INTEGER | **Citing** publication ID | The newer patent |
| `cited_pat_publn_id` | INTEGER | **Cited** publication ID | The older patent being referenced |
| `citn_id` | INTEGER | Citation ID within citing document | Unique per citation |
| `citn_origin` | CHAR(5) | Origin of citation | **Filter for examiner (SEA)** |
| `cited_pat_publn_dt` | DATE | Publication date of cited patent | Temporal analysis |
| `cited_npl_publn_id` | INTEGER | Non-patent literature ID (if applicable) | We ignore NPL |

**Citation Origins (Critical):**

| Origin Code | Meaning | Reliability | PatentIQ Use |
|-------------|---------|-------------|--------------|
| **SEA** | Search/Examination | **High** - examiner-generated | **Primary focus** |
| **EXAM** | Examination only | High - examiner-generated | Include |
| **APP** | Applicant | Low - may be strategic | Use with caution |
| **OPP** | Opposition | Medium - challenger-generated | Include for opposed patents |
| **ISR** | International Search Report | High - examiner-generated | Include |
| **{other}** | Various | Variable | Generally exclude |

**Direction of Citations:**

```
Forward Citations (for patent A):
    Patent B cites A
    Patent C cites A
    → A has 2 forward citations

Backward Citations (for patent A):
    A cites Patent X
    A cites Patent Y
    → A has 2 backward citations
```

**Get Forward Citations:**
```sql
SELECT 
    cited.publn_nr as patent_being_analyzed,
    citing.publn_nr as patent_citing_it,
    c.citn_origin,
    c.cited_pat_publn_dt
FROM tls212_citation c
JOIN tls211_pat_publn cited ON c.cited_pat_publn_id = cited.pat_publn_id
JOIN tls211_pat_publn citing ON c.pat_publn_id = citing.pat_publn_id
WHERE cited.publn_nr = '1234567'
  AND cited.publn_auth = 'EP'
  AND c.citn_origin = 'SEA'
ORDER BY c.cited_pat_publn_dt;
```

**Get Backward Citations:**
```sql
SELECT 
    citing.publn_nr as patent_being_analyzed,
    cited.publn_nr as patent_it_cites,
    c.citn_origin
FROM tls212_citation c
JOIN tls211_pat_publn citing ON c.pat_publn_id = citing.pat_publn_id
JOIN tls211_pat_publn cited ON c.cited_pat_publn_id = cited.pat_publn_id
WHERE citing.publn_nr = '1234567'
  AND citing.publn_auth = 'EP'
  AND c.citn_origin IN ('SEA', 'EXAM', 'APP')
ORDER BY cited.publn_date;
```

**PatentIQ Use:**
- **Influence dimension:** Forward citation count, velocity, H-index
- **Backward quality:** Diversity, self-citation rate, prior art freshness
- **ML features:** Citation counts by year

---

### 4.2 TLS215_CITN_CATEG (Citation Categories)

**Purpose:** Examiner-assigned categories for citations (X, Y, A, etc.).

**Key Fields:**

| Field | Type | Description | PatentIQ Use |
|-------|------|-------------|--------------|
| `pat_publn_id` | INTEGER | **Citing** publication | Composite key |
| `citn_id` | INTEGER | Citation ID | Composite key |
| `citn_categ` | CHAR(1) | **Category (X, Y, A, etc.)** | **Blocking evidence** |
| `relevant_claim` | INTEGER | Which claim this applies to | Claim-level analysis |
| `citn_replenished` | INTEGER | Data quality flag | Filter if needed |

**Primary Key:** (`pat_publn_id`, `citn_id`, `citn_categ`, `relevant_claim`)

**Why Composite Key?**
- One citation can have multiple categories (X for claim 1, Y for claim 3)
- Multiple rows per citation possible

**Critical Issue - Data Structure:**
```
Patent EP2000000 (citing) cites EP1000000 (cited)

TLS212_CITATION:
pat_publn_id: 200000, citn_id: 5, cited_pat_publn_id: 100000

TLS215_CITN_CATEG (multiple rows for same citation):
pat_publn_id: 200000, citn_id: 5, citn_categ: X, relevant_claim: 1
pat_publn_id: 200000, citn_id: 5, citn_categ: X, relevant_claim: 3
pat_publn_id: 200000, citn_id: 5, citn_categ: Y, relevant_claim: 5
```

**Deduplication Required:**
- Claim-level rows must be aggregated
- Count unique citations, not category rows

**Get X/Y Citations (Deduplicated):**
```sql
SELECT 
    cited.publn_nr as blocker_patent,
    COUNT(DISTINCT c.citn_id) as unique_xy_citations,
    COUNT(DISTINCT CASE WHEN cat.citn_categ = 'X' THEN c.citn_id END) as x_citations,
    COUNT(DISTINCT CASE WHEN cat.citn_categ = 'Y' THEN c.citn_id END) as y_citations
FROM tls212_citation c
JOIN tls215_citn_categ cat ON 
    c.pat_publn_id = cat.pat_publn_id AND 
    c.citn_id = cat.citn_id
JOIN tls211_pat_publn cited ON c.cited_pat_publn_id = cited.pat_publn_id
WHERE cited.publn_auth = 'EP'
  AND cited.publn_kind IN ('B1', 'B2')
  AND cat.citn_categ IN ('X', 'Y')
  AND c.citn_origin = 'SEA'
GROUP BY cited.publn_nr;
```

**PatentIQ Use:**
- **Identify blocking patents:** Patents cited as X/Y demonstrate blocking power
- **Not primary metric** (coverage issues), but useful enrichment
- **Data quality validation:** Check coverage before relying on it

---

## 5. PATSTAT Family Tables

### 5.1 TLS218_DOCDB_FAM (Simple Families)

**Purpose:** Groups related applications into patent families.

**Key Fields:**

| Field | Type | Description | PatentIQ Use |
|-------|------|-------------|--------------|
| `docdb_family_id` | INTEGER | **Family identifier** | Group patents |
| `appln_id` | INTEGER | **Application in family** | Member patents |

**Family Concept:**
```
One invention → Filed in multiple countries

Original: DE application (priority)
    ↓
EP application (EPO)
US application (USPTO)
JP application (JPO)
    ↓
All share same docdb_family_id
```

**Get Family Members:**
```sql
SELECT 
    fam.docdb_family_id,
    p.publn_auth as country,
    p.publn_nr as patent_number,
    p.publn_kind,
    a.appln_filing_date
FROM tls218_docdb_fam fam
JOIN tls201_appln a ON fam.appln_id = a.appln_id
JOIN tls211_pat_publn p ON a.appln_id = p.appln_id
WHERE fam.docdb_family_id = (
    SELECT docdb_family_id 
    FROM tls218_docdb_fam 
    WHERE appln_id = (
        SELECT appln_id 
        FROM tls211_pat_publn 
        WHERE publn_nr = '1234567' AND publn_auth = 'EP'
    )
)
AND p.publn_kind LIKE '%B%';  -- Granted patents only
```

**PatentIQ Uses:**
1. **Geographic coverage:** How many countries protect this invention?
2. **Strategic value:** Larger family = more investment = likely more valuable
3. **Legal strength:** Family size is a scoring component
4. **Financial analysis:** Each country has separate maintenance costs

**Family Size Distribution:**
- Typical: 1-5 countries
- Strategic: 5-15 countries (US, EP, JP, CN, KR core)
- High-value: 20+ countries

---

## 6. INPADOC Legal Events

### 6.1 Legal Events Overview

**INPADOC** (International Patent Documentation) provides legal status and events.

**Accessed Through:** PATSTAT Global edition integrates INPADOC data.

**Key Event Types:**

| Event Type | Description | PatentIQ Use |
|------------|-------------|--------------|
| **OPPOSITION** | Third-party challenge filed | **Legal strength indicator** |
| **OPPOSITION_OUTCOME** | Opposition result (maintained/revoked/amended) | **Key quality signal** |
| **FEE_PAYMENT** | Annual renewal fee paid | **Renewal behavior tracking** |
| **LAPSE** | Patent lapses (fees not paid) | **Abandonment detection** |
| **LIMITATION** | Patent scope limited | Legal strength adjustment |
| **TRANSFER** | Change of ownership | Ownership tracking |
| **LICENSE** | Licensing agreement recorded | **Validation data for licensing algorithm** |

### 6.2 Opposition Events

**Query Opposition Status:**
```sql
-- Simplified example (actual table structure varies by PATSTAT version)
SELECT 
    p.publn_nr,
    le.event_type,
    le.event_date,
    le.event_status
FROM tls211_pat_publn p
JOIN tls201_appln a ON p.appln_id = a.appln_id
JOIN legal_events_table le ON a.appln_id = le.appln_id
WHERE p.publn_nr = '1234567'
  AND le.event_type LIKE '%OPPOSITION%'
ORDER BY le.event_date;
```

**Opposition Outcomes:**
- **MAINTAINED:** Patent survives unchanged → Strong signal ✅
- **MAINTAINED_AMENDED:** Patent survives with changes → Moderate
- **REVOKED:** Patent invalidated → Weak signal ❌
- **WITHDRAWN:** Opponent withdraws → Ambiguous (settlement? weak opposition?)

**PatentIQ Legal Strength Score:**
```python
if opposition_outcome == "MAINTAINED":
    opposition_score = 25  # Maximum points
elif opposition_outcome == "MAINTAINED_AMENDED":
    opposition_score = 15  # Moderate points
elif opposition_outcome == "REVOKED":
    opposition_score = 0   # No points
else:  # No opposition
    opposition_score = 15  # Baseline (no challenge)
```

### 6.3 Renewal/Fee Payment Events

**Renewal Tracking:**
```sql
SELECT 
    p.publn_nr,
    le.event_date,
    le.event_type,
    EXTRACT(YEAR FROM le.event_date) - a.appln_filing_year as renewal_year
FROM tls211_pat_publn p
JOIN tls201_appln a ON p.appln_id = a.appln_id
JOIN legal_events_table le ON a.appln_id = le.appln_id
WHERE p.publn_nr = '1234567'
  AND le.event_type = 'FEE_PAYMENT'
ORDER BY le.event_date;
```

**Renewal Analysis:**
- **Years renewed:** Count of fee payment events (starts Year 3)
- **Consistency:** Gaps indicate owner hesitation or late payments
- **Compared to age:** 12 years renewed out of 12 possible = 100% rate

**PatentIQ Renewal Score:**
```python
renewal_rate = years_renewed / max_possible_renewal_years

if renewal_rate == 1.0:
    renewal_score = 25  # Perfect record
elif renewal_rate >= 0.8:
    renewal_score = 20  # Strong
elif renewal_rate >= 0.6:
    renewal_score = 15  # Moderate
else:
    renewal_score = 10  # Weak/inconsistent
```

### 6.4 Licensing Events

**PatentIQ Validation Use:**
- Cross-check our licensing predictions against known deals
- INPADOC records some (not all) licensing agreements
- Used in automated validation (no manual expert needed)

---

## 7. PatentIQ Data Requirements Map

### 7.1 Data Requirements by Feature

| Feature | Required Tables | Key Fields | Purpose |
|---------|----------------|------------|---------|
| **Patent Metadata** | TLS201_APPLN, TLS211_PAT_PUBLN | filing_date, grant_date, publn_nr | Basic info, age calculation |
| **Forward Citations** | TLS212_CITATION | cited_pat_publn_id, citn_origin | Influence scoring |
| **Backward Citations** | TLS212_CITATION | pat_publn_id, cited_pat_publn_id | Quality analysis |
| **X/Y Citations** | TLS212_CITATION, TLS215_CITN_CATEG | citn_categ | Blocking evidence (optional) |
| **Technology Class** | TLS224_APPLN_CPC | cpc_class_symbol | Field normalization, ML feature |
| **Assignee** | TLS206_PERSON, TLS207_PERS_APPLN | person_name, applt_seq_nr | Portfolio analysis, licensing |
| **Patent Family** | TLS218_DOCDB_FAM | docdb_family_id | Geographic coverage |
| **Oppositions** | INPADOC legal events | event_type, event_status | Legal strength |
| **Renewals** | INPADOC legal events | event_type, event_date | Legal & financial strength |
| **Claim Count** | TLS211_PAT_PUBLN (or TLS214) | publn_claims | Legal scope |

### 7.2 Data Pipeline Overview

```
Source: PATSTAT PostgreSQL
    ↓
Extract: Daily batch jobs
    ↓
Transform: 
  - Join tables
  - Deduplicate X/Y citations
  - Calculate derived metrics
    ↓
Load: Parquet Data Lake
    ↓
Serve: 
  - Redis Cache (L1 - 24h TTL)
  - Parquet (L2 - permanent)
  - PATSTAT (L3 - fallback)
```

**Parquet Files Created:**

| File | Source Tables | Purpose | Update Frequency |
|------|---------------|---------|------------------|
| `patents.parquet` | TLS201, TLS211, TLS206, TLS207 | Core metadata | Daily |
| `citations.parquet` | TLS212 | Forward/backward citations | Daily |
| `xy_citations.parquet` | TLS212, TLS215 (deduplicated) | X/Y blocking citations | Daily |
| `legal_events.parquet` | INPADOC | Oppositions, renewals | Daily |
| `families.parquet` | TLS218 | Family members | Weekly |
| `cpc_codes.parquet` | TLS224 | Technology classifications | Weekly |
| `features.parquet` | All (computed) | ML feature vectors | On-demand |

---

## 8. Query Patterns & Examples

### 8.1 Common Query Patterns

#### **Pattern 1: Get Patent Metadata**

```sql
SELECT 
    p.publn_nr as patent_number,
    p.publn_kind,
    p.publn_date as grant_date,
    a.appln_filing_date as filing_date,
    a.appln_filing_year,
    EXTRACT(YEAR FROM AGE(p.publn_date, a.appln_filing_date)) as years_to_grant,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.publn_date)) as age_since_grant,
    pers.person_name as assignee,
    a.granted
FROM tls211_pat_publn p
JOIN tls201_appln a ON p.appln_id = a.appln_id
LEFT JOIN tls207_pers_appln link ON a.appln_id = link.appln_id AND link.applt_seq_nr > 0
LEFT JOIN tls206_person pers ON link.person_id = pers.person_id
WHERE p.publn_nr = '1234567'
  AND p.publn_auth = 'EP'
  AND p.publn_kind IN ('B1', 'B2');
```

#### **Pattern 2: Count Forward Citations**

```sql
SELECT 
    cited.publn_nr,
    COUNT(DISTINCT c.citn_id) as total_citations,
    COUNT(DISTINCT CASE WHEN c.citn_origin = 'SEA' THEN c.citn_id END) as examiner_citations,
    COUNT(DISTINCT CASE WHEN c.citn_origin = 'APP' THEN c.citn_id END) as applicant_citations,
    MIN(citing.publn_date) as first_citation_date,
    MAX(citing.publn_date) as latest_citation_date
FROM tls212_citation c
JOIN tls211_pat_publn cited ON c.cited_pat_publn_id = cited.pat_publn_id
JOIN tls211_pat_publn citing ON c.pat_publn_id = citing.pat_publn_id
WHERE cited.publn_nr = '1234567'
  AND cited.publn_auth = 'EP'
GROUP BY cited.publn_nr;
```

#### **Pattern 3: Get Company Portfolio**

```sql
WITH target_company AS (
    SELECT person_id
    FROM tls206_person
    WHERE person_name LIKE '%Siemens AG%'
    LIMIT 1
)
SELECT 
    p.publn_nr,
    p.publn_date,
    a.appln_filing_year,
    cpc.cpc_class_symbol,
    COUNT(DISTINCT c.citn_id) as forward_citations
FROM target_company tc
JOIN tls207_pers_appln link ON tc.person_id = link.person_id
JOIN tls201_appln a ON link.appln_id = a.appln_id
JOIN tls211_pat_publn p ON a.appln_id = p.appln_id
LEFT JOIN tls224_appln_cpc cpc ON a.appln_id = cpc.appln_id AND cpc.cpc_position = 'F'
LEFT JOIN tls212_citation c ON p.pat_publn_id = c.cited_pat_publn_id AND c.citn_origin = 'SEA'
WHERE link.applt_seq_nr > 0
  AND p.publn_auth = 'EP'
  AND p.publn_kind IN ('B1', 'B2')
  AND a.appln_filing_year >= 2015
GROUP BY p.publn_nr, p.publn_date, a.appln_filing_year, cpc.cpc_class_symbol
ORDER BY p.publn_date DESC;
```

#### **Pattern 4: Technology Landscape (Key Players)**

```sql
SELECT 
    pers.person_name,
    COUNT(DISTINCT p.pat_publn_id) as patent_count,
    AVG(citation_counts.cites) as avg_citations,
    MIN(a.appln_filing_year) as first_filing,
    MAX(a.appln_filing_year) as latest_filing
FROM tls224_appln_cpc cpc
JOIN tls201_appln a ON cpc.appln_id = a.appln_id
JOIN tls211_pat_publn p ON a.appln_id = p.appln_id
JOIN tls207_pers_appln link ON a.appln_id = link.appln_id AND link.applt_seq_nr > 0
JOIN tls206_person pers ON link.person_id = pers.person_id
LEFT JOIN LATERAL (
    SELECT COUNT(DISTINCT citn_id) as cites
    FROM tls212_citation
    WHERE cited_pat_publn_id = p.pat_publn_id
      AND citn_origin = 'SEA'
) citation_counts ON true
WHERE cpc.cpc_class_symbol LIKE 'A61B%'  -- Medical devices
  AND p.publn_kind IN ('B1', 'B2')
  AND a.appln_filing_year >= 2015
  AND pers.psn_sector = 'COMPANY'
GROUP BY pers.person_name
HAVING COUNT(DISTINCT p.pat_publn_id) >= 5
ORDER BY patent_count DESC
LIMIT 20;
```

#### **Pattern 5: Patent Family Geography**

```sql
WITH base_patent AS (
    SELECT appln_id, publn_nr
    FROM tls211_pat_publn
    WHERE publn_nr = '1234567' AND publn_auth = 'EP'
),
family AS (
    SELECT docdb_family_id
    FROM tls218_docdb_fam
    WHERE appln_id = (SELECT appln_id FROM base_patent)
)
SELECT 
    p.publn_auth as country,
    p.publn_nr,
    p.publn_kind,
    a.appln_filing_date,
    p.publn_date
FROM family f
JOIN tls218_docdb_fam fam ON f.docdb_family_id = fam.docdb_family_id
JOIN tls201_appln a ON fam.appln_id = a.appln_id
JOIN tls211_pat_publn p ON a.appln_id = p.appln_id
WHERE p.publn_kind LIKE '%B%'  -- Granted patents
ORDER BY p.publn_auth, p.publn_date;
```

### 8.2 Performance-Critical Queries

#### **Optimized Citation Count (Batch)**

```sql
-- For batch processing (100+ patents)
WITH patents AS (
    SELECT pat_publn_id, publn_nr
    FROM tls211_pat_publn
    WHERE publn_nr = ANY(ARRAY['1234567', '2345678', '3456789'])
      AND publn_auth = 'EP'
)
SELECT 
    p.publn_nr,
    COUNT(DISTINCT c.citn_id) FILTER (WHERE c.citn_origin = 'SEA') as citations
FROM patents p
LEFT JOIN tls212_citation c ON p.pat_publn_id = c.cited_pat_publn_id
GROUP BY p.publn_nr;
```

**Why This is Fast:**
- Uses `ANY(ARRAY[...])` instead of multiple `WHERE` clauses
- `FILTER` clause avoids separate queries per origin
- Indexes on `cited_pat_publn_id` and `citn_origin`

---

## 9. Performance Optimization

### 9.1 Indexing Strategy

**Critical Indexes (already present in PATSTAT):**

```sql
-- Most important for PatentIQ
CREATE INDEX idx_citation_cited ON tls212_citation(cited_pat_publn_id);
CREATE INDEX idx_citation_citing ON tls212_citation(pat_publn_id);
CREATE INDEX idx_publn_nr ON tls211_pat_publn(publn_nr, publn_auth);
CREATE INDEX idx_appln_filing_year ON tls201_appln(appln_filing_year);
CREATE INDEX idx_cpc_symbol ON tls224_appln_cpc(cpc_class_symbol);
CREATE INDEX idx_person_name ON tls206_person(person_name);
```

### 9.2 Query Optimization Tips

**1. Always Filter Early:**
```sql
-- GOOD
WHERE p.publn_auth = 'EP' 
  AND p.publn_kind IN ('B1', 'B2')
  AND a.appln_filing_year >= 2015

-- BAD (filters after joins)
```

**2. Use EXISTS Instead of JOIN for Existence Checks:**
```sql
-- GOOD
WHERE EXISTS (
    SELECT 1 FROM tls212_citation c
    WHERE c.cited_pat_publn_id = p.pat_publn_id
)

-- BAD
JOIN tls212_citation c ON p.pat_publn_id = c.cited_pat_publn_id
-- (when you just need to know IF citations exist)
```

**3. Limit Result Sets:**
```sql
-- For large portfolios, process in batches
LIMIT 1000 OFFSET 0;
```

**4. Use EXPLAIN ANALYZE:**
```sql
EXPLAIN ANALYZE
SELECT ... your query ...;
```

### 9.3 Parquet Benefits

**Why We Use Parquet:**
- **Columnar storage:** Read only needed columns
- **Compression:** 10x smaller than CSV
- **Type safety:** Schema enforced
- **Fast filtering:** Predicate pushdown

**Parquet vs. PostgreSQL:**
- **Parquet:** 10-100x faster for analytical queries (scans, aggregations)
- **PostgreSQL:** Better for transactional queries (point lookups, updates)

**PatentIQ Strategy:**
- **Extract** from PostgreSQL (slow, complete data)
- **Transform** and store in Parquet (fast, analytics-optimized)
- **Serve** from Parquet for analysis (fast queries)

---

## 10. Data Quality & Validation

### 10.1 Common Data Quality Issues

**1. NULL Citation Categories:**
- **Issue:** ~10-15% of examiner citations lack category in TLS215
- **Impact:** X/Y analysis coverage reduced
- **Mitigation:** Document coverage, use what's available

**2. Name Variants:**
- **Issue:** "Siemens AG" vs. "Siemens Aktiengesellschaft"
- **Impact:** Portfolio analysis misses patents
- **Mitigation:** Use `han_id` for grouping, fuzzy matching

**3. Delayed Data:**
- **Issue:** 6-12 month lag in PATSTAT
- **Impact:** Recent patents missing or incomplete
- **Mitigation:** Document cutoff date, use EP Register API for real-time

**4. Claim Count Availability:**
- **Issue:** Not all publications have `publn_claims` populated
- **Impact:** Legal strength score incomplete
- **Mitigation:** Use EP Register API as fallback

**5. Duplicate Publications:**
- **Issue:** B1 and B2 for same patent (after opposition amendments)
- **Impact:** Citation double-counting
- **Mitigation:** Use `publn_first_grant = 'Y'` or latest publication

### 10.2 Data Validation Queries

**Check Coverage - X/Y Citations:**
```sql
SELECT 
    COUNT(DISTINCT p.pat_publn_id) as total_patents,
    COUNT(DISTINCT CASE WHEN xy.pat_publn_id IS NOT NULL THEN p.pat_publn_id END) as patents_with_xy,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN xy.pat_publn_id IS NOT NULL THEN p.pat_publn_id END) / 
          COUNT(DISTINCT p.pat_publn_id), 2) as coverage_pct
FROM tls211_pat_publn p
JOIN tls201_appln a ON p.appln_id = a.appln_id
LEFT JOIN (
    SELECT DISTINCT c.cited_pat_publn_id as pat_publn_id
    FROM tls212_citation c
    JOIN tls215_citn_categ cat ON c.pat_publn_id = cat.pat_publn_id AND c.citn_id = cat.citn_id
    WHERE cat.citn_categ IN ('X', 'Y')
      AND c.citn_origin = 'SEA'
) xy ON p.pat_publn_id = xy.pat_publn_id
WHERE p.publn_auth = 'EP'
  AND p.publn_kind IN ('B1', 'B2')
  AND a.appln_filing_year BETWEEN 2015 AND 2020;
```

**Check NULL Categories:**
```sql
SELECT 
    COUNT(*) as total_examiner_citations,
    COUNT(CASE WHEN cat.citn_categ IS NULL THEN 1 END) as null_categories,
    ROUND(100.0 * COUNT(CASE WHEN cat.citn_categ IS NULL THEN 1 END) / COUNT(*), 2) as null_pct
FROM tls212_citation c
LEFT JOIN tls215_citn_categ cat ON 
    c.pat_publn_id = cat.pat_publn_id AND c.citn_id = cat.citn_id
WHERE c.citn_origin = 'SEA';
```

**Validate Patent Age Calculation:**
```sql
SELECT 
    p.publn_nr,
    a.appln_filing_date,
    p.publn_date,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.publn_date)) as age_years,
    EXTRACT(YEAR FROM AGE(p.publn_date, a.appln_filing_date)) as years_to_grant
FROM tls211_pat_publn p
JOIN tls201_appln a ON p.appln_id = a.appln_id
WHERE p.publn_nr = '1234567' AND p.publn_auth = 'EP';
```

### 10.3 Data Quality Acceptance Criteria

| Metric | Target | Minimum Acceptable | Action if Below Minimum |
|--------|--------|-------------------|------------------------|
| X/Y Coverage (2015-2020) | >35% | >25% | Simplify to binary flag or defer feature |
| NULL Categories | <15% | <20% | Document limitation, proceed |
| Duplicate Patents | <5% | <10% | Deduplicate using publn_first_grant |
| Missing Claim Counts | <20% | <30% | Use EP Register API fallback |
| Name Harmonization | >80% | >70% | Manual disambiguation for top companies |

---

## 11. Quick Reference

### 11.1 Table Cheat Sheet

| Need | Table(s) | Key Join |
|------|----------|----------|
| Patent metadata | TLS201_APPLN, TLS211_PAT_PUBLN | appln_id |
| Forward citations | TLS212_CITATION | cited_pat_publn_id |
| Backward citations | TLS212_CITATION | pat_publn_id |
| X/Y categories | TLS215_CITN_CATEG | (pat_publn_id, citn_id) |
| Technology class | TLS224_APPLN_CPC | appln_id |
| Assignee | TLS206_PERSON, TLS207_PERS_APPLN | person_id, appln_id |
| Family | TLS218_DOCDB_FAM | appln_id, docdb_family_id |
| Oppositions | INPADOC legal events | appln_id |
| Renewals | INPADOC legal events | appln_id |

### 11.2 Common Filters

```sql
-- EPO granted patents only
WHERE p.publn_auth = 'EP'
  AND p.publn_kind IN ('B1', 'B2')

-- Recent patents (2015 onwards)
WHERE a.appln_filing_year >= 2015

-- Examiner citations only
WHERE c.citn_origin = 'SEA'

-- Main CPC code only
WHERE cpc.cpc_position = 'F'

-- Applicants (not just inventors)
WHERE link.applt_seq_nr > 0

-- Companies (not individuals)
WHERE pers.psn_sector = 'COMPANY'
```

---

**This database tutorial should serve as the primary reference for all database-related queries in PatentIQ development. Bookmark it and refer back frequently.**

**Next Steps:**
1. Explore PATSTAT interactively using provided queries
2. Run validation queries to understand data quality
3. Begin implementing data extraction for Parquet pipeline

**Related Documentation:**
- [[02-Education|Education Guide]] - Concepts explained
- [[PRD-Data-Requirements|Data Requirements PRD]] - Detailed specifications
- [[PRD-Data-Validation|Data Validation PRD]] - Quality assurance


---

## 6.4 Financial Data Extraction from INPADOC

**Purpose:** Extract renewal payment history to calculate costs and predict abandonment risk.

### Renewal Fee Payments Query

INPADOC legal events record when renewal fees are paid. This is **critical** for our Financial dimension.

```sql
-- Get renewal payment history for a patent
SELECT 
    p.publn_nr,
    a.appln_filing_date,
    le.event_date as payment_date,
    EXTRACT(YEAR FROM le.event_date) - EXTRACT(YEAR FROM a.appln_filing_date) as renewal_year,
    le.event_status,
    le.event_code
FROM tls211_pat_publn p
JOIN tls201_appln a ON p.appln_id = a.appln_id
JOIN legal_events_table le ON a.appln_id = le.appln_id
WHERE p.publn_nr = '1234567'
  AND p.publn_auth = 'EP'
  AND le.event_type IN ('FEE_PAYMENT', 'ANNUAL_FEE', 'RENEWAL')
ORDER BY le.event_date;
```

**Expected Output:**
```
publn_nr  | filing_date | payment_date | renewal_year | event_status
----------|-------------|--------------|--------------|-------------
1234567   | 2015-03-15  | 2018-03-15   | 3            | PAID
1234567   | 2015-03-15  | 2019-03-15   | 4            | PAID
1234567   | 2015-03-15  | 2020-03-15   | 5            | PAID
...
1234567   | 2015-03-15  | 2024-03-15   | 9            | PAID
```

**PatentIQ Use:**
1. **Years Renewed:** Count of payment events (9 in example above)
2. **Renewal Consistency:** Check for gaps (missing years)
3. **Latest Renewal:** Most recent payment date
4. **Projected Renewals:** Years 10-20 if pattern continues

### Calculate Renewal Costs to Date

Once we have renewal history, calculate actual costs using EPO fee schedule:

```python
# EPO Renewal Fee Schedule (2024)
EPO_RENEWAL_FEES = {
    3: 465,
    4: 580,
    5: 810,
    6: 1040,
    7: 1155,
    8: 1265,
    9: 1380,
    10: 1560,
    # Years 10+ all €1,560
}

def calculate_epo_renewal_costs(renewal_years: List[int]) -> float:
    """
    Calculate total EPO renewal fees paid to date
    
    Args:
        renewal_years: List of years for which fees were paid (e.g., [3, 4, 5, 6, 7, 8, 9])
    
    Returns:
        Total cost in EUR
    """
    total_cost = 0
    
    for year in renewal_years:
        if year <= 9:
            total_cost += EPO_RENEWAL_FEES[year]
        else:
            total_cost += 1560  # Years 10+ constant
    
    return total_cost

# Example:
renewal_history = [3, 4, 5, 6, 7, 8, 9]
epo_costs = calculate_epo_renewal_costs(renewal_history)
# Result: 465 + 580 + 810 + 1040 + 1155 + 1265 + 1380 = €6,695
```

### Detect Lapsed/Abandoned Patents

```sql
-- Find patents that lapsed (stopped paying fees)
SELECT 
    p.publn_nr,
    a.appln_filing_date,
    MAX(le.event_date) as last_renewal_payment,
    EXTRACT(YEAR FROM MAX(le.event_date)) - EXTRACT(YEAR FROM a.appln_filing_date) as last_year_paid,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, a.appln_filing_date)) as current_age,
    CASE 
        WHEN EXTRACT(YEAR FROM MAX(le.event_date)) - EXTRACT(YEAR FROM a.appln_filing_date) 
             < EXTRACT(YEAR FROM AGE(CURRENT_DATE, a.appln_filing_date)) - 1
        THEN 'LIKELY_LAPSED'
        ELSE 'ACTIVE'
    END as status
FROM tls211_pat_publn p
JOIN tls201_appln a ON p.appln_id = a.appln_id
LEFT JOIN legal_events_table le ON a.appln_id = le.appln_id 
    AND le.event_type IN ('FEE_PAYMENT', 'ANNUAL_FEE', 'RENEWAL')
WHERE p.publn_auth = 'EP'
  AND p.publn_kind IN ('B1', 'B2')
  AND a.appln_filing_year >= 2015
GROUP BY p.publn_nr, a.appln_filing_date
HAVING MAX(le.event_date) IS NOT NULL;
```

**Logic:**
- If last payment was Year 9, but patent is now Year 12 → Likely lapsed
- Gap of 2+ years between last payment and current age → Abandoned

---

## 6.5 Geographic Coverage for Financial Analysis

**Purpose:** Determine which countries the patent is validated in to calculate national costs.

### Get Family Countries

```sql
-- Get all countries where patent is validated (granted)
WITH base_patent AS (
    SELECT appln_id, publn_nr
    FROM tls211_pat_publn
    WHERE publn_nr = '1234567' 
      AND publn_auth = 'EP'
      AND publn_kind IN ('B1', 'B2')
),
family AS (
    SELECT docdb_family_id
    FROM tls218_docdb_fam
    WHERE appln_id = (SELECT appln_id FROM base_patent)
)
SELECT 
    p.publn_auth as country_code,
    p.publn_nr as country_patent_number,
    p.publn_kind,
    p.publn_date as grant_date,
    a.appln_filing_date
FROM family f
JOIN tls218_docdb_fam fam_members ON f.docdb_family_id = fam_members.docdb_family_id
JOIN tls201_appln a ON fam_members.appln_id = a.appln_id
JOIN tls211_pat_publn p ON a.appln_id = p.appln_id
WHERE p.publn_kind LIKE '%B%'  -- Granted patents only
ORDER BY p.publn_auth;
```

**Expected Output:**
```
country_code | country_patent_number | publn_kind | grant_date  | filing_date
-------------|----------------------|------------|-------------|------------
DE           | 602015001234         | B1         | 2017-08-20  | 2015-03-15
EP           | 1234567              | B1         | 2017-06-15  | 2015-03-15
FR           | 1234567              | B1         | 2017-06-15  | 2015-03-15
GB           | 1234567              | B1         | 2017-06-15  | 2015-03-15
IT           | 1234567              | B1         | 2017-06-15  | 2015-03-15
```

**Interpretation:**
- EP grant automatically covers EPO member states
- Must **validate** in each country (DE, FR, GB, IT, etc.)
- Each validation has costs: translation + local filing
- Each country then requires **separate annual renewal fees**

### Financial Data Reference Files (External)

**File: `data/reference/fee_schedules.json`**

```json
{
  "epo_fees_2024": {
    "filing": 130,
    "search": 1400,
    "examination": 1880,
    "grant": 1020,
    "renewal": {
      "3": 465,
      "4": 580,
      "5": 810,
      "6": 1040,
      "7": 1155,
      "8": 1265,
      "9": 1380,
      "10": 1560
    }
  },
  "national_validation": {
    "DE": 800,
    "FR": 700,
    "GB": 600,
    "IT": 550,
    "ES": 500,
    "NL": 450,
    "BE": 400,
    "CH": 750,
    "AT": 400,
    "SE": 600
  },
  "national_renewal_formulas": {
    "DE": {
      "base": 70,
      "increment_per_year": 50,
      "description": "€70 + (year - 3) * €50"
    },
    "FR": {
      "base": 42,
      "increment_per_year": 25,
      "description": "€42 + (year - 3) * €25"
    },
    "GB": {
      "base": 50,
      "increment_per_year": 30,
      "description": "€50 + (year - 3) * €30"
    }
  },
  "attorney_fee_multiplier": 1.3,
  "prosecution_cost_estimate": {
    "simple": 3000,
    "average": 5000,
    "complex": 15000
  }
}
```

**Source:** EPO Official Journal, national patent office websites (public data)

**Update Frequency:** Annually (fees typically change January 1st)

---

## 6.6 Complete Financial Data Pipeline

### FinancialDataCollector Class

```python
class FinancialDataCollector:
    """
    Collects all financial data for a patent from PATSTAT/INPADOC
    """
    
    def __init__(self, db_session, fee_schedule_path: str):
        self.db = db_session
        self.fees = self._load_fee_schedule(fee_schedule_path)
    
    def collect_financial_data(self, patent_id: str) -> dict:
        """
        Collect all financial data needed for Financial Engine
        
        Returns:
            {
                'filing_costs': float,
                'prosecution_costs': float,  # Estimated
                'grant_costs': float,
                'validation_costs': float,
                'epo_renewal_costs': float,
                'national_renewal_costs': float,
                'total_cost_to_date': float,
                'annual_maintenance_current': float,
                'projected_lifetime_cost': float,
                'renewal_history': List[int],
                'family_countries': List[str],
                'years_renewed': int,
                'patent_age': int
            }
        """
        
        # 1. Get patent metadata
        patent = self._get_patent_metadata(patent_id)
        
        # 2. Get renewal history from INPADOC
        renewal_history = self._get_renewal_history(patent['appln_id'])
        
        # 3. Get family countries
        family_countries = self._get_family_countries(patent['appln_id'])
        
        # 4. Calculate costs
        filing_costs = self.fees['epo_fees_2024']['filing'] + \
                      self.fees['epo_fees_2024']['search'] + \
                      self.fees['epo_fees_2024']['examination']
        
        prosecution_costs = self.fees['prosecution_cost_estimate']['average']
        grant_costs = self.fees['epo_fees_2024']['grant']
        
        validation_costs = sum(
            self.fees['national_validation'].get(c, 500)
            for c in family_countries if c != 'EP'
        )
        
        epo_renewal_costs = sum(
            self.fees['epo_fees_2024']['renewal'].get(str(year), 1560)
            for year in renewal_history
        )
        
        national_renewal_costs = self._calculate_national_renewals(
            family_countries, renewal_history
        )
        
        total_cost = (
            filing_costs +
            prosecution_costs +
            grant_costs +
            validation_costs +
            epo_renewal_costs +
            national_renewal_costs
        ) * self.fees['attorney_fee_multiplier']
        
        # 5. Current annual maintenance
        current_year = patent['patent_age']
        annual_epo = self.fees['epo_fees_2024']['renewal'].get(
            str(current_year), 1560
        )
        annual_national = sum(
            self._calculate_national_fee(c, current_year)
            for c in family_countries if c != 'EP'
        )
        annual_maintenance = (annual_epo + annual_national) * \
                            self.fees['attorney_fee_multiplier']
        
        # 6. Projected lifetime cost
        remaining_years = 20 - patent['patent_age']
        projected_future = self._project_future_costs(
            family_countries,
            current_year,
            remaining_years
        )
        projected_lifetime = total_cost + projected_future
        
        return {
            'filing_costs': filing_costs,
            'prosecution_costs': prosecution_costs,
            'grant_costs': grant_costs,
            'validation_costs': validation_costs,
            'epo_renewal_costs': epo_renewal_costs,
            'national_renewal_costs': national_renewal_costs,
            'total_cost_to_date': total_cost,
            'annual_maintenance_current': annual_maintenance,
            'projected_lifetime_cost': projected_lifetime,
            'renewal_history': renewal_history,
            'family_countries': family_countries,
            'years_renewed': len(renewal_history),
            'patent_age': patent['patent_age']
        }
    
    def _get_renewal_history(self, appln_id: int) -> List[int]:
        """
        Query INPADOC for renewal payment years
        
        Returns list like [3, 4, 5, 6, 7, 8, 9]
        """
        query = """
        SELECT DISTINCT
            EXTRACT(YEAR FROM le.event_date) - EXTRACT(YEAR FROM a.appln_filing_date) as renewal_year
        FROM tls201_appln a
        JOIN legal_events_table le ON a.appln_id = le.appln_id
        WHERE a.appln_id = :appln_id
          AND le.event_type IN ('FEE_PAYMENT', 'ANNUAL_FEE', 'RENEWAL')
        ORDER BY renewal_year
        """
        
        result = self.db.execute(query, {'appln_id': appln_id})
        return [row.renewal_year for row in result]
    
    def _get_family_countries(self, appln_id: int) -> List[str]:
        """
        Query TLS218_DOCDB_FAM for family member countries
        
        Returns list like ['EP', 'DE', 'FR', 'GB']
        """
        query = """
        WITH family AS (
            SELECT docdb_family_id
            FROM tls218_docdb_fam
            WHERE appln_id = :appln_id
        )
        SELECT DISTINCT p.publn_auth as country
        FROM family f
        JOIN tls218_docdb_fam fam ON f.docdb_family_id = fam.docdb_family_id
        JOIN tls201_appln a ON fam.appln_id = a.appln_id
        JOIN tls211_pat_publn p ON a.appln_id = p.appln_id
        WHERE p.publn_kind LIKE '%B%'
        """
        
        result = self.db.execute(query, {'appln_id': appln_id})
        return [row.country for row in result]
    
    def _calculate_national_fee(self, country: str, year: int) -> float:
        """Calculate annual renewal fee for a country"""
        if country not in self.fees['national_renewal_formulas']:
            # Default formula
            return 50 + (year - 3) * 25
        
        formula = self.fees['national_renewal_formulas'][country]
        base = formula['base']
        increment = formula['increment_per_year']
        
        if year < 3:
            return 0
        
        return min(base + (year - 3) * increment, 1000)  # Cap at €1000
    
    def _calculate_national_renewals(
        self,
        countries: List[str],
        years: List[int]
    ) -> float:
        """Calculate total national renewal costs"""
        total = 0
        for country in countries:
            if country == 'EP':
                continue
            for year in years:
                total += self._calculate_national_fee(country, year)
        return total
    
    def _project_future_costs(
        self,
        countries: List[str],
        current_year: int,
        remaining_years: int
    ) -> float:
        """Project future costs to Year 20"""
        future_cost = 0
        
        for year in range(current_year + 1, min(current_year + remaining_years + 1, 21)):
            epo_fee = self.fees['epo_fees_2024']['renewal'].get(str(year), 1560)
            national_fees = sum(
                self._calculate_national_fee(c, year)
                for c in countries if c != 'EP'
            )
            future_cost += (epo_fee + national_fees) * \
                          self.fees['attorney_fee_multiplier']
        
        return future_cost
```

---

## 6.7 Financial Data Summary

### Data Sources Table

| Data Type | Source | Access Method | Update Frequency |
|-----------|--------|---------------|------------------|
| **Renewal History** | INPADOC legal events | SQL query on `legal_events_table` | Real-time (with 6-month lag) |
| **Family Countries** | TLS218_DOCDB_FAM | SQL query via `docdb_family_id` | Weekly batch update |
| **EPO Fee Schedule** | EPO Official Journal | JSON file (`fee_schedules.json`) | Annually (Jan 1) |
| **National Fees** | National patent offices | JSON formulas | Annually |
| **Validation Costs** | Industry surveys | JSON static values | Annually |

### Complete Cost Calculation Example

```python
# Patent: EP1234567B1
# Filed: 2015-03-15, Granted: 2017-06-15
# Current Age: 9 years (as of 2024)
# Family: EP, DE, FR, GB
# Renewals Paid: Years 3-9

financial_data = collector.collect_financial_data('EP1234567B1')

# Results:
{
    'filing_costs': 3410,              # Filing + search + examination
    'prosecution_costs': 5000,         # Estimated average
    'grant_costs': 1020,               # EPO grant fee
    'validation_costs': 2100,          # DE(800) + FR(700) + GB(600)
    'epo_renewal_costs': 6695,         # Sum Y3-9: 465+580+810+1040+1155+1265+1380
    'national_renewal_costs': 3339,    # DE + FR + GB for Y3-9
    'total_cost_to_date': 28235,       # Sum all × 1.3 attorney multiplier
    'annual_maintenance_current': 2992,# Current year (Y10) cost
    'projected_lifetime_cost': 58450,  # To Year 20
    'renewal_history': [3,4,5,6,7,8,9],
    'family_countries': ['EP','DE','FR','GB'],
    'years_renewed': 7,
    'patent_age': 9
}

# Cost per citation (if 25 forward citations):
cost_per_citation = 28235 / 25  # €1,129 per citation (very efficient!)
```

This financial data feeds directly into the **Financial Engine** for scoring and optimization recommendations.

---

**Key Takeaway:** Financial data comes from **three sources**:
1. **INPADOC** (renewal history) - database queries
2. **TLS218** (family geography) - database queries  
3. **Fee schedules** (costs) - external reference files

All three are combined to calculate total costs, current obligations, and future projections.
