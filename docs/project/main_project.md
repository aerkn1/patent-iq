# PatentIQ - Main Product Requirements Document (PRD)

**Version:** 2.0  
**Date:** December 2024  
**Status:** Approved for Implementation  
**Project Duration:** 12 Weeks  
**Team Size:** 4 Developers

---

## 1. Executive Summary

### 1.1 Product Vision

**PatentIQ** is an AI-powered patent intelligence platform that combines 4D analytics (Technical Influence + Legal Strength + Financial Value + Future Potential) with licensing intelligence to deliver actionable insights for patent portfolio management.

### 1.2 Core Innovation

- **4D Framework:** First platform to integrate technical, legal, financial, and predictive dimensions
- **Licensing Intelligence:** Automated potential licensee identification (unique in market)
- **Financial Optimization:** ROI-driven portfolio pruning recommendations
- **ML Predictions:** Citation forecasting with SHAP explainability

### 1.3 Target Market

**Primary Users:**
1. IP Portfolio Managers - Portfolio optimization, cost reduction
2. Patent Attorneys - Licensing opportunity identification
3. Technology Transfer Offices - Commercialization strategy
4. IP Investors - M&A due diligence, valuation

**Market Size:** Global IP management software market ~$3.2B, growing 12% annually

---

## 2. Product Objectives

### 2.1 Business Goals

1. **Win the IP Analytics Contest** - Demonstrate novel approach to patent valuation
2. **Validate 4D Framework** - Prove multi-dimensional analysis provides superior insights
3. **Showcase Automation** - Demonstrate 1000x speed advantage over manual analysis
4. **Generate Licensing Leads** - Identify €500K+ in licensing opportunities per portfolio

### 2.2 Success Metrics

**Technical Metrics:**
- Single patent analysis: <5 seconds (90th percentile)
- Portfolio analysis (50 patents): <60 seconds
- ML prediction R²: >0.65
- System uptime: >99% during demo week

**Business Metrics:**
- Hidden gems identified: 5-15% of portfolios
- Cost optimization: 20-30% savings identified
- Licensing candidates: 5-10 per patent
- User satisfaction: Actionable insights in 100% of analyses

---

## 3. Complete Use Cases

### UC-01: Single Patent Deep Analysis

**Primary Actor:** IP Manager

**Preconditions:**
- User has EPO patent number
- Patent exists in PATSTAT database
- System has analyzed patent (or can analyze in <5s)

**Main Flow:**
1. User enters patent number (e.g., "EP1234567B1")
2. System validates patent format and existence
3. System retrieves or calculates 4D scores:
   - **Technical Influence:** Citations, H-index, backward analysis
   - **Legal Strength:** Oppositions, renewals, claims, family
   - **Financial Value:** Costs, ROI, geographic efficiency
   - **Future Potential:** ML prediction, market trends
4. System synthesizes assessment into one of 6 categories
5. System identifies top 5 potential licensees
6. System provides market context (industry, competitors)
7. User reviews comprehensive dashboard
8. User exports PDF report (optional)

**Postconditions:**
- User has complete patent intelligence
- Analysis cached for 24 hours
- User can drill down to any dimension

**Alternative Flows:**
- **3a.** Patent lacks some data → System uses best available, marks confidence
- **3b.** ML prediction unavailable → Skip future dimension
- **5a.** No suitable licensees found → Show market players only

**Success Criteria:**
- Analysis completion: <5 seconds (uncached)
- All 4 dimensions calculated
- Synthesis category assigned
- At least 3 actionable insights provided

---

### UC-02: Company Portfolio Analysis

**Primary Actor:** IP Portfolio Manager

**Preconditions:**
- User knows company name or has patent list
- Company has patents in PATSTAT

**Main Flow:**
1. User searches company name (e.g., "Siemens AG")
2. System performs fuzzy search, returns disambiguated options
3. User selects correct entity
4. System retrieves all EPO patents for assignee
5. User applies optional filters (year range, CPC section, status)
6. System analyzes portfolio:
   - Aggregate 4D metrics across portfolio
   - Distribution analysis (by category, CPC, geography)
   - Financial overview (total costs, optimization opportunities)
   - Licensing opportunities (portfolio-wide)
   - Competitive positioning
7. System generates portfolio dashboard with visualizations
8. User drills down to individual patents
9. User exports portfolio report (PDF/CSV)

**Postconditions:**
- Portfolio analyzed and cached
- Optimization recommendations generated
- User has prioritized action list

**Alternative Flows:**
- **3a.** Pre-computed company (top 50) → Instant results (<2s)
- **3b.** New company → Full analysis or sample (user choice)
- **4a.** Large portfolio (>500 patents) → User selects subset

**Success Criteria:**
- Portfolio analysis (50 patents): <60 seconds
- Optimization savings identified: >15% of annual costs
- Distribution charts render correctly
- Export functionality works

---

### UC-03: Manual Portfolio Upload

**Primary Actor:** IP Manager with custom portfolio

**Main Flow:**
1. User uploads CSV file with patent numbers (max 500)
2. System validates file format and patent numbers
3. System reports validation results:
   - Valid patents count
   - Invalid patents (with reasons)
   - Duplicate patents detected
4. User reviews validation report
5. User confirms to proceed or corrects file
6. System processes valid patents (same as UC-02, steps 6-9)
7. User reviews portfolio analysis
8. User exports results

**Success Criteria:**
- Upload validation: <10 seconds
- Clear error messages for invalid patents
- Analysis (100 patents): <2 minutes
- CSV export includes all metrics

---

### UC-04: Licensing Opportunity Discovery

**Primary Actor:** Technology Transfer Officer

**Main Flow:**
1. User views analyzed patent (from UC-01)
2. System displays "Licensing Intelligence" section
3. System shows for each potential licensee:
   - Company name and country
   - Fit score (0-100) with explanation
   - Filing activity in relevant technology
   - Geographic presence alignment
   - IP sophistication indicators
   - Estimated licensing value range
4. User selects a potential licensee for details
5. System shows detailed company profile:
   - Recent patent activity
   - Technology focus areas
   - Licensing history
   - Contact strategy rationale
6. User exports licensing report
7. User flags companies for outreach

**Success Criteria:**
- 5-10 potential licensees identified
- Fit scores justify rankings
- Licensing value estimates reasonable
- Export includes contact rationale

---

### UC-05: Portfolio Financial Optimization

**Primary Actor:** CFO / IP Portfolio Manager

**Main Flow:**
1. User views portfolio dashboard (from UC-02)
2. System highlights "Optimization Opportunities" panel
3. System categorizes patents:
   - **Abandonment candidates:** High cost, low value (savings if abandoned)
   - **Geographic optimization:** Trim specific countries (selective savings)
   - **Strategic holds:** High value despite costs (maintain)
4. User reviews recommendations with risk assessment
5. System shows financial impact simulation:
   - Annual savings per action
   - Total portfolio savings
   - Value retention percentage
   - Risk scoring per patent
6. User runs "what-if" scenarios (e.g., abandon bottom 10%)
7. System recalculates portfolio metrics
8. User exports optimization roadmap
9. User flags patents for renewal/abandonment decisions

**Success Criteria:**
- Savings identified: 20-30% of annual maintenance
- Risk assessment included for each recommendation
- Simulation responds in <2 seconds
- Recommendation acceptance rate: >60%

---

### UC-06: Hidden Gems Discovery

**Primary Actor:** IP Manager / Patent Attorney

**Main Flow:**
1. User views portfolio dashboard
2. System automatically identifies "Hidden Gems":
   - Low citation count (<20 forward citations)
   - High legal strength (>70/100)
   - High financial efficiency (<€2,000 per citation)
   - Strong renewal behavior
3. System displays hidden gems list with highlights
4. User clicks on individual hidden gem
5. System explains why it's undervalued:
   - Specific legal strengths (e.g., opposition survived)
   - Cost efficiency compared to peers
   - Potential licensing opportunities
6. System suggests strategic actions:
   - Licensing targets (specific companies)
   - Enforcement opportunities
   - Portfolio positioning strategy
7. User exports hidden gems report

**Success Criteria:**
- Hidden gems: 5-15% of typical portfolio
- Explanations are specific and actionable
- At least 3 licensing targets per hidden gem
- Report includes valuation estimate

---

### UC-07: Market Intelligence

**Primary Actor:** Business Development Manager

**Main Flow:**
1. User views patent or portfolio analysis
2. System displays "Market Analysis" section
3. For single patent:
   - Applicable markets (CPC-mapped industries)
   - Primary market with size/growth data
   - Key players (top 20 by patent count)
   - Competitive intensity score
   - Technology trend (growing/stable/declining)
4. For portfolio:
   - Markets covered across portfolio
   - Market concentration analysis
   - Competitive positioning vs. top players
   - White space opportunities (uncovered markets)
5. User filters by geography or CPC section
6. User compares company position to competitors
7. System shows technology landscape visualization
8. User exports market intelligence report

**Success Criteria:**
- Market mapping accuracy: >85% (validated against industry classifications)
- Competitor identification: Top 90% by patent count captured
- Market size data from credible sources
- Visualizations render correctly

---

### UC-08: ML-Powered Future Prediction

**Primary Actor:** IP Strategist

**Main Flow:**
1. User views "Future Potential" dimension
2. System displays ML prediction results:
   - Predicted citations (3-year horizon)
   - Confidence interval (95%)
   - Trend classification (Growing/Stable/Declining)
   - Top 3 prediction drivers (SHAP values)
3. User clicks "Why this prediction?"
4. System shows SHAP explanation:
   - Each feature's contribution to prediction
   - Direction of impact (positive/negative)
   - Magnitude of influence
5. User compares prediction across portfolio
6. System identifies "Rising Stars" (high predicted growth)
7. User exports prediction report with feature importance

**Success Criteria:**
- Prediction accuracy: 70% within ±3 citations
- SHAP values sum to total prediction
- Top 3 drivers explain >60% of prediction
- Trend classification accuracy: >65%

---

## 4. System Architecture

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│  - Streamlit UI (Multi-page)            │
│  - PDF Report Generator                 │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Application Layer               │
│  - FastAPI REST API                     │
│  - Request Validation                   │
│  - Response Formatting                  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Business Logic Layer            │
│  - Influence Engine                     │
│  - Legal Strength Engine                │
│  - Financial Engine                     │
│  - Future Engine (ML)                   │
│  - Synthesis Engine                     │
│  - Licensing Intelligence               │
│  - Portfolio Aggregator                 │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         ML Model Layer                  │
│  - LightGBM Citation Predictor          │
│  - SHAP Explainer                       │
│  - Feature Engineering Pipeline         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Data Access Layer               │
│  - Patent Repository                    │
│  - Citation Repository                  │
│  - Feature Store                        │
│  - Redis Cache                          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Data Layer                      │
│  - PATSTAT (PostgreSQL)                 │
│  - Parquet Data Lake                    │
│  - Reference Data (JSON/CSV)            │
└─────────────────────────────────────────┘
```

### 4.2 Architecture Patterns

**Layered Architecture:**
- Strict unidirectional dependencies (outer → inner)
- Domain layer independent of infrastructure
- Dependency injection for testability

**Repository Pattern:**
- Abstract data access behind interfaces
- Swappable data sources
- Testable with mocks

**Engine Pattern (Strategy):**
- Interchangeable scoring algorithms
- Each engine implements BaseEngine interface
- Configurable at runtime

**Caching Strategy (Read-Through):**
- L1: Redis (24h TTL) - Full analysis results
- L2: Parquet (permanent) - Pre-computed features
- L3: Memory (request lifetime) - Hot data

---

## 5. Technology Stack

### 5.1 Core Technologies

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | Streamlit | 1.30+ | Rapid UI development |
| **Backend** | FastAPI | 0.109+ | REST API |
| **Database** | PostgreSQL | 14+ | PATSTAT storage |
| **Data Processing** | Polars | 0.20+ | Fast DataFrames |
| **Storage** | Parquet | - | Columnar storage |
| **Cache** | Redis | 7.0+ | Result caching |
| **ML Framework** | LightGBM | 4.1+ | Gradient boosting |
| **Explainability** | SHAP | 0.44+ | Feature importance |
| **Visualization** | Plotly | 5.18+ | Interactive charts |

### 5.2 Development Tools

| Tool | Purpose |
|------|---------|
| Python 3.11+ | Primary language |
| Docker | Containerization |
| MyPy | Type checking |
| Ruff | Linting & formatting |
| Pytest | Testing framework |
| Structlog | Structured logging |

---

## 6. Data Requirements Overview

### 6.1 Primary Data Sources

**PATSTAT (PostgreSQL):**
- Patent applications (TLS201_APPLN)
- Patent publications (TLS211_PAT_PUBLN)
- Citations (TLS212_CITATION)
- Citation categories (TLS215_CITN_CATEG)
- Assignees (TLS206_PERSON)
- CPC classifications (TLS224_APPLN_CPC)
- Patent families (TLS218_DOCDB_FAM)

**Coverage:** ~500,000 EPO granted patents (2015-2024)

**INPADOC (via PATSTAT):**
- Legal events (oppositions, renewals, licensing)
- Priority claims
- Technology fields

**External Reference Data:**
- EPO fee schedules (JSON)
- CPC-to-industry mapping (CSV)
- Market size data (JSON)

### 6.2 Preprocessed Data Lake

**Parquet Storage Structure:**
```
data/processed/
├── patents.parquet          # Core patent metadata
├── citations.parquet        # All citations (forward/backward)
├── legal_events.parquet     # Oppositions, renewals
├── families.parquet         # Patent families
├── features.parquet         # Pre-computed ML features (33 features)
└── cache/                   # Analysis result cache
```

**Expected Data Volume:**
- Patents: ~500K rows × 25 columns = ~50MB
- Citations: ~5M rows = ~200MB
- Features: ~50K rows × 42 columns = ~10MB

---

## 7. Key Features Summary

### 7.1 The 4D Framework

**Dimension 1: Technical Influence (0-100)**
- Forward citations count
- Backward citations quality analysis
- Citation velocity
- H-index calculation
- Field-normalized impact

**Dimension 2: Legal Strength (0-100)**
- Grant status and prosecution quality
- Opposition outcomes
- Renewal behavior and consistency
- Patent family size and strategic coverage
- Claim count (scope indicator)

**Dimension 3: Financial Value (0-100)**
- Total cost to date calculation
- Cost per citation efficiency
- Geographic ROI by country
- Abandonment risk scoring
- Annual savings potential

**Dimension 4: Future Potential (0-100)**
- ML citation prediction (3-year horizon)
- Confidence intervals
- Trend classification
- SHAP feature explanations
- Market context integration

### 7.2 Unique Differentiators

**🌟 Licensing Intelligence (Unique to PatentIQ):**
- Automated potential licensee identification
- Fit scoring (0-100) based on 5 factors
- Estimated licensing value ranges
- Contact strategy recommendations

**🌟 Financial Optimization (Unique to PatentIQ):**
- Portfolio-wide cost optimization
- Abandonment candidate identification
- Geographic efficiency analysis
- Annual savings quantification

**🌟 Hidden Gems Detection:**
- Automated identification of undervalued patents
- Low citations + high legal/financial value
- Licensing opportunity prioritization

**🌟 Fully Automated Analysis:**
- No manual scoring required
- 1000x faster than manual review
- Consistent methodology across all patents

---

## 8. ML Model Specifications

### 8.1 Citation Prediction Model

**Model Type:** LightGBM Regressor (Poisson objective)

**Feature Set:** 33 base features → 42 after one-hot encoding
- 8 traditional citation features
- 6 legal features
- 5 financial features
- 3 market features
- 3 backward citation quality features
- 3 technology features
- 2 family features
- 2 temporal features
- 9 CPC one-hot encoded features

**Training Data:**
- Training set: 50,000 patents (2010-2016 filings)
- Validation set: 10,000 patents (2017-2018 filings)
- Target: Citations received 3 years post-observation

**Performance Targets:**
- R² > 0.65 (target: 0.70)
- RMSE < 4.5 citations
- 70% of predictions within ±3 citations

**Explainability:**
- SHAP TreeExplainer for all predictions
- Top 3 feature drivers highlighted
- Feature importance exported

---

## 9. Synthesis Categories

The system classifies every patent into one of 6 categories:

| Category | Criteria | Priority | Recommendation |
|----------|----------|----------|----------------|
| **CROWN_JEWEL** | Influence >70, Legal >70, Financial >60 | CRITICAL_ASSET | RENEW_ALL - Top priority |
| **HIDDEN_GEM** | Influence <50, Legal >70, Financial efficient | UNDERVALUED | STRATEGIC_HOLD - Licensing opportunity |
| **COST_DRAIN** | Financial score <30 or Abandonment risk >70% | ABANDONMENT_CANDIDATE | ABANDON - Save costs |
| **GEOGRAPHIC_INEFFICIENCY** | Good patent but wasteful geography | OPTIMIZE | RENEW_SELECTIVE - Trim countries |
| **RISING_STAR** | Future trend GROWING, predicted >15 cites | MONITOR_INVESTMENT | RENEW_ALL - Increasing value |
| **AGING_ASSET** | Influence >60, Future DECLINING, High abandon risk | REVIEW_REQUIRED | REVIEW - Consider strategic abandonment |

---

## 10. Implementation Timeline

### 10.1 12-Week Schedule

| Week | Focus Area | Key Deliverables | Critical Path |
|------|-----------|------------------|---------------|
| **1-2** | Data Setup + Core Engines | Legal & Financial Engines, Parquet lake | ✓ |
| **3-4** | Influence + Feature Engineering | Influence Engine, ML features (33) | ✓ |
| **5-6** | ML Training + Validation | Trained model (R²>0.65), automated validation | ✓ |
| **7-8** | Synthesis + Licensing | Synthesis Engine, Licensing Intelligence | ✓ |
| **9-10** | Portfolio Features | Portfolio dashboard, company search, pre-compute top 50 | ✓ |
| **11** | Testing + Performance | Integration tests, optimization, case studies | ✓ |
| **12** | Final Polish + Demo | Documentation, demo prep, contest submission | ✓ |

### 10.2 Team Structure

**Developer 1 (Data Lead):**
- PATSTAT data extraction
- Feature engineering
- Financial calculations
- Licensing intelligence

**Developer 2 (Algorithm Lead):**
- Legal Strength Engine
- Influence Engine
- Synthesis Engine
- Testing

**Developer 3 (ML Lead):**
- ML model training
- SHAP integration
- Future Engine
- FastAPI development

**Developer 4 (Frontend Lead):**
- Streamlit UI
- Visualizations
- PDF export
- UX/UI polish

---

## 11. Success Criteria

### 11.1 Technical Acceptance

| Metric | Target | Minimum |
|--------|--------|---------|
| Single patent analysis time | <5s | <10s |
| Portfolio analysis (50 patents) | <60s | <120s |
| ML R² score | >0.65 | >0.60 |
| Test coverage | >70% | >60% |
| API uptime (demo week) | >99% | >95% |

### 11.2 Business Acceptance

| Deliverable | Status |
|-------------|--------|
| 10 case studies analyzed | Required |
| 3+ hidden gems identified per portfolio | Required |
| €50K+ savings shown in portfolio optimization | Required |
| 5 potential licensees per patent (average) | Required |
| Working demo for all use cases | Required |

### 11.3 Contest Submission

| Item | Format | Pages/Duration |
|------|--------|----------------|
| Technical whitepaper | PDF | 10 pages |
| User guide | PDF | 5 pages |
| Presentation deck | PPTX | 10 slides |
| Demo video | MP4 | 3 minutes |
| Source code | GitHub | Complete |
| Validation evidence | JSON + PDF | Comprehensive |

---

## 12. Competitive Positioning

### 12.1 vs. Existing Solutions

| Feature | PatentIQ | PatSnap | Clarivate | Others |
|---------|----------|---------|-----------|--------|
| 4D Framework | ✅ | ❌ | ❌ | ❌ |
| ML Predictions | ✅ | ❌ | ❌ | ⚠️ Basic |
| Financial Optimization | ✅ **Unique** | ❌ | ❌ | ❌ |
| Licensing Intelligence | ✅ **Unique** | ❌ | ❌ | ❌ |
| Fully Automated | ✅ | ⚠️ Partial | ⚠️ Partial | ❌ Manual |
| Hidden Gems Detection | ✅ | ❌ | ❌ | ❌ |

### 12.2 Value Proposition

**For IP Managers:**
> "Analyze 500 patents in minutes, not months. Identify 20-30% cost savings and discover hidden licensing opportunities worth €500K+."

**For CFOs:**
> "Data-driven portfolio optimization: reduce maintenance costs by €100K+ annually while preserving strategic value."

**For Technology Transfer:**
> "Automated licensee matching: identify the top 5 companies most likely to license each patent, with estimated deal values."

---

## 13. Risk Management

### 13.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| ML R² < 0.60 | Medium | High | Fallback: Focus on descriptive analytics only |
| Portfolio analysis too slow | Medium | High | Pre-compute top 50 companies, offer sampling |
| PATSTAT query performance | Medium | Medium | Parquet caching, query optimization |
| Data quality issues | Low | Medium | Automated validation, graceful degradation |

### 13.2 Project Risks

| Risk | Mitigation |
|------|------------|
| Scope creep | Weekly reviews, strict feature freeze Week 11 |
| Team member unavailable | Cross-training, pair programming |
| Timeline delays | Critical path monitoring, weekly checkpoints |
| Demo failures | Extensive testing, backup plans, pre-recorded video |

---

## 14. Next Steps

### 14.1 Immediate Actions (Week 1)

1. ✅ Set up development environment
2. ✅ Access PATSTAT production database
3. ✅ Run initial data validation queries
4. ✅ Create project repository structure
5. ✅ Assign team roles and responsibilities

### 14.2 Week 1 Deliverables

- Data validation report (coverage, quality metrics)
- Parquet data lake structure created
- Legal Strength Engine (v0.1)
- UI component library initialized
- Weekly standup schedule established

### 14.3 Key Decision Points

**Week 2 Checkpoint:** Data quality GO/NO-GO
- If data coverage <20% → Pivot strategy
- If quality issues severe → Simplify features

**Week 6 Checkpoint:** ML validation results
- If R² improvement <5% → Remove prediction feature
- If performance acceptable → Proceed with full scope

**Week 11 Checkpoint:** Feature freeze
- No new features after this point
- Focus on testing, optimization, demo prep

---

## 15. Appendices

### 15.1 Related Documentation

- **[[02-Education]]** - Terminology and concepts guide
- **[[03-Database-Tutorial]]** - PATSTAT/INPADOC reference
- **[[PRD-Data-Requirements]]** - Detailed data specifications
- **[[PRD-Data-Validation]]** - Validation framework
- **[[PRD-Testing-Strategy]]** - Test suite guidelines
- **[[PRD-ML-Guidelines]]** - ML model specifications

### 15.2 External References

- PATSTAT Documentation: https://www.epo.org/patstat
- EPO Fee Schedules: https://www.epo.org/fees
- WIPO CPC Concordance: https://www.wipo.int/classifications
- LightGBM Documentation: https://lightgbm.readthedocs.io
- SHAP Documentation: https://shap.readthedocs.io

### 15.3 Glossary

See **[[02-Education]]** for comprehensive terminology guide.

---

**Document Status:** ✅ Approved for Implementation  
**Last Updated:** December 2024  
**Next Review:** Week 6 (ML Validation Checkpoint)  
**Owner:** Project Lead

---

*This PRD provides the high-level overview. For detailed technical specifications, refer to the specialized PRD documents linked above.*
