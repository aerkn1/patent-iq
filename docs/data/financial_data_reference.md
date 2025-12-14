# Financial Data - Quick Reference

**Quick answer to "Where does financial data come from?"**

## Three Data Sources

### 1. INPADOC (Renewal History) 📊
**Database Table:** `legal_events_table`  
**Query For:** Renewal fee payment dates  
**Gives Us:** Which years were renewed (e.g., [3,4,5,6,7,8,9])

```sql
SELECT renewal_year FROM legal_events 
WHERE event_type = 'FEE_PAYMENT'
```

### 2. TLS218_DOCDB_FAM (Family Geography) 🌍
**Database Table:** `TLS218_DOCDB_FAM`  
**Query For:** Countries where patent is validated  
**Gives Us:** Country list (e.g., ['EP','DE','FR','GB'])

```sql
SELECT DISTINCT country FROM patent_family
WHERE docdb_family_id = X
```

### 3. Fee Schedules (External Reference) 💰
**File:** `data/reference/fee_schedules.json`  
**Source:** EPO Official Journal + national offices (public data)  
**Gives Us:** Official fee amounts by year and country

```json
{
  "epo_renewal": {"3": 465, "10": 1560},
  "national_validation": {"DE": 800, "FR": 700}
}
```

## Calculation Flow

```
1. Query INPADOC → Get years renewed [3,4,5,6,7,8,9]
2. Query TLS218 → Get countries ['EP','DE','FR','GB']
3. Load fee_schedules.json → Get official rates
4. Apply formulas:
   - EPO costs = sum(fees[year] for year in renewals)
   - National costs = sum(fees[country][year] for all combinations)
   - Validation = one-time cost per country
   - Filing/prosecution/grant = standard estimates
5. Total = (all costs) × 1.3 (attorney multiplier)
6. Cost per citation = total / forward_citations
```

## Example Calculation

**Patent:** EP1234567B1  
**Renewed:** Years 3-9 (7 renewals)  
**Countries:** EP, DE, FR, GB (4 jurisdictions)  
**Forward Citations:** 25

**Costs:**
- Filing/prosecution/grant: €11,020
- EPO renewals (Y3-9): €6,695
- National renewals (Y3-9): €3,339
- Validation (DE,FR,GB): €2,100
- **Subtotal:** €23,154
- **With attorney fees (×1.3):** €30,100
- **Cost per citation:** €1,204

**Score:** 88/100 (Efficient - below field average of €2,500/citation)

## Related Documentation

- **Complete queries:** [[03-Database-Tutorial#6-4-financial-data-extraction-from-inpadoc|Database Tutorial §6.4-6.7]]
- **Concepts:** [[02-Education#5-financial-aspects|Education Guide §5]]
- **Implementation:** See PRD-Data-Requirements (coming next)

## Common Pitfalls

❌ **Don't** estimate all costs arbitrarily  
✅ **Do** use actual renewal history + real geography

❌ **Don't** forget attorney fee multiplier (~1.3×)  
✅ **Do** account for professional fees on top of official fees

❌ **Don't** ignore national renewal fees  
✅ **Do** remember each country requires separate renewals

❌ **Don't** assume all years cost the same  
✅ **Do** use year-specific fee schedules (escalating)

## Validation

Our cost estimates validated against public company disclosures:
- Mean error: 18.2%
- 78% within ±20% of actual
- Correlation: 0.87 with disclosed budgets

**Source:** See Validation Framework in PRD-Data-Validation
