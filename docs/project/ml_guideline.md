# PRD: ML Guidelines - Model Training & Deployment

**Document Version:** 1.0  
**Last Updated:** December 2024  
**Status:** Approved for Implementation  
**Related Documents:** [[02-Education]], [[PRD-Data-Requirements]], [[PRD-Service-Layers]]

---

## Table of Contents

1. [Overview](https://claude.ai/chat/9e811d76-e932-4b05-8b8a-7bc5ccb1b726#1-overview)
2. [ML Problem Specification](https://claude.ai/chat/9e811d76-e932-4b05-8b8a-7bc5ccb1b726#2-ml-problem-specification)
3. [Feature Engineering](https://claude.ai/chat/9e811d76-e932-4b05-8b8a-7bc5ccb1b726#3-feature-engineering)
4. [Data Preparation](https://claude.ai/chat/9e811d76-e932-4b05-8b8a-7bc5ccb1b726#4-data-preparation)
5. [Model Training](https://claude.ai/chat/9e811d76-e932-4b05-8b8a-7bc5ccb1b726#5-model-training)
6. [Model Validation](https://claude.ai/chat/9e811d76-e932-4b05-8b8a-7bc5ccb1b726#6-model-validation)
7. [Model Deployment](https://claude.ai/chat/9e811d76-e932-4b05-8b8a-7bc5ccb1b726#7-model-deployment)
8. [Explainability & SHAP](https://claude.ai/chat/9e811d76-e932-4b05-8b8a-7bc5ccb1b726#8-explainability--shap)
9. [Fallback Strategies](https://claude.ai/chat/9e811d76-e932-4b05-8b8a-7bc5ccb1b726#9-fallback-strategies)
10. [Monitoring & Maintenance](https://claude.ai/chat/9e811d76-e932-4b05-8b8a-7bc5ccb1b726#10-monitoring--maintenance)

---

## 1. Overview

### 1.1 Purpose

This document provides **complete specifications** for training, validating, and deploying the citation prediction ML model for PatentIQ's Future Potential dimension.

**Analogy:** Just as a pharmaceutical company has rigorous protocols for drug development (testing, trials, approval), we have protocols for ML model development.

### 1.2 ML Philosophy

**Principle 1: Explainability Over Accuracy**

A model that scores 70% accuracy with explanations beats 75% without.

```python
# ✅ Good: Lower accuracy, but explainable
model = LightGBM(max_depth=8)  # Shallow trees = interpretable
shap_explainer = SHAP(model)

# ❌ Bad: Higher accuracy, black box
model = DeepNeuralNetwork(layers=50)  # Cannot explain why
```

**Why:** Users need to **trust** predictions. "Because the model said so" isn't acceptable for IP decisions.

**Principle 2: Temporal Validation**

Never train on future data, always validate on time-held-out data.

**Principle 3: Production First**

Design for production from day one, not as afterthought.

### 1.3 ML Problem Statement

**Goal:** Predict number of forward citations a patent will receive in next 3 years

**Input:** Patent P filed in year Y, Features F(P) computed as of year (Y + 3)  
**Output:** Predicted citations between year (Y+3) and year (Y+6)

**Example:**

```
Patent filed: 2015
Observation year: 2018 (3 years later)
Features: Citations 2015-2018, grant status, etc.
Target: Citations 2018-2021 (next 3 years)
```

---

## 2. ML Problem Specification

### 2.1 Problem Type

**Regression** (predict continuous value: citation count)

**Distribution:** Poisson (citations are count data)

**Why Poisson:**

- Citations are discrete, non-negative integers
- Events are relatively rare (most patents get <20 citations)
- Poisson regression fits this naturally

### 2.2 Success Metrics

**Primary Metric: R² (Coefficient of Determination)**

Target: **R² > 0.65** (minimum: 0.60)

**Secondary Metrics:**

|Metric|Formula|Target|
|---|---|---|
|RMSE|sqrt(mean((y_true - y_pred)²))|< 4.5 citations|
|MAE|mean(\|y_true - y_pred\|)|< 3.0 citations|
|Accuracy@3|% within ±3 of actual|> 70%|

**Baseline Comparison:**

Must beat these baselines:

- Mean baseline: R² ~0.15
- Linear trend: R² ~0.35
- Age-adjusted mean: R² ~0.45

---

## 3. Feature Engineering

### 3.1 Feature Overview

**Total: 42 features** across 8 categories

```
┌──────────────────────────────────────┐
│ 42 ML Features                       │
├──────────────────────────────────────┤
│ 1. Historical Citations:  8 features │
│ 2. Technology:            12 features│
│ 3. Legal:                 6 features │
│ 4. Family:                2 features │
│ 5. Financial:             5 features │
│ 6. Market:                3 features │
│ 7. Temporal:              2 features │
│ 8. Calculated:            4 features │
└──────────────────────────────────────┘
```

### 3.2 Historical Citation Features (8 features)

**Why:** Past predicts future - citation patterns continue

|Feature|Type|Range|Why Important|
|---|---|---|---|
|citations_year1|Int|0-100|Early impact indicator|
|citations_year2|Int|0-100|Growth trajectory|
|citations_year3|Int|0-100|Recent momentum|
|citation_velocity|Float|0-20|Rate of accumulation|
|citation_acceleration|Float|-10 to 10|Trend direction|
|backward_citations|Int|0-100|Research quality|
|backward_self_cite_rate|Float|0-1|Self-reliance|
|backward_diversity|Float|0-1|Prior art breadth|

**Feature Engineering Code:**

```python
def create_historical_features(patent: Patent, observation_year: int) -> dict:
    filing_year = patent.filing_date.year
    citations = patent.citations
    
    # Citations by year
    citations_y1 = sum(1 for c in citations if c.citation_date.year == filing_year + 1)
    citations_y2 = sum(1 for c in citations if c.citation_date.year == filing_year + 2)
    citations_y3 = sum(1 for c in citations if c.citation_date.year == filing_year + 3)
    
    # Velocity
    age = observation_year - filing_year
    total_citations = citations_y1 + citations_y2 + citations_y3
    velocity = total_citations / age if age > 0 else 0
    
    # Acceleration (slope)
    acceleration = (citations_y3 - citations_y1) / 2 if citations_y1 > 0 else 0
    
    # Backward citations
    backward = patent.backward_citations
    self_cites = sum(1 for c in backward if c.is_self_citation)
    self_cite_rate = self_cites / len(backward) if backward else 0
    
    return {
        'citations_year1': citations_y1,
        'citations_year2': citations_y2,
        'citations_year3': citations_y3,
        'citation_velocity': velocity,
        'citation_acceleration': acceleration,
        'backward_citations': len(backward),
        'backward_self_cite_rate': self_cite_rate,
        'backward_diversity': 1 - self_cite_rate
    }
```

### 3.3 Technology Features (3 + 9 one-hot = 12 features)

|Feature|Type|Why Important|
|---|---|---|
|cpc_count|Int|Interdisciplinary breadth|
|cpc_density|Float|Technology overlap intensity|
|cpc_section|Categorical|Field normalization|
|cpc_section_A...Y (9)|Binary|One-hot encoding for LightGBM|

**One-Hot Encoding:**

```python
def one_hot_encode_cpc(cpc_section: str) -> dict:
    sections = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'Y']
    return {
        f'cpc_section_{section}': 1 if cpc_section == section else 0
        for section in sections
    }
```

### 3.4 Legal Features (6 features)

|Feature|Type|Why Important|
|---|---|---|
|is_granted|Binary|Only granted patents get cited|
|has_opposition|Binary|Quality signal|
|opposition_survived|Binary|Strength confirmation|
|is_renewed|Binary|Owner confidence|
|renewal_years|Int|Longevity expectation|
|claim_count|Int|Scope breadth|

### 3.5 Family Features (2 features)

|Feature|Type|Why Important|
|---|---|---|
|family_size|Int|Strategic value indicator|
|has_us_family|Binary|US market importance|

### 3.6 Financial Features (5 features)

|Feature|Type|Why Important|
|---|---|---|
|total_cost|Float|Investment signal|
|cost_per_citation|Float|Efficiency indicator|
|geographic_efficiency|Float|Value optimization|
|renewal_consistency|Float|Owner commitment|
|cost_trajectory|Float|Sustainability|

### 3.7 Market Features (3 features)

|Feature|Type|Why Important|
|---|---|---|
|market_size_usd_b|Float|Larger market = more R&D|
|market_growth_rate|Float|Growth drives citations|
|competitive_intensity|Float|Competition breeds citations|

### 3.8 Temporal Features (2 features)

|Feature|Type|Why Important|
|---|---|---|
|filing_year|Int|Time-based trends|
|filing_season|Categorical|Seasonal patterns|

### 3.9 Calculated Features (4 features)

|Feature|Type|Calculation|
|---|---|---|
|age_at_observation|Int|obs_year - filing_year|
|years_since_grant|Int|obs_year - grant_year|
|tech_market_overlap|Float|CPC-market alignment|
|quality_signal|Float|Composite legal/financial|

### 3.10 Feature Importance (Expected)

```
Top 10 Features (Expected):
1. citations_year3          18%
2. citation_velocity        15%
3. market_growth_rate       12%
4. citations_year2          11%
5. is_granted                9%
6. backward_citations        7%
7. family_size               6%
8. claim_count               5%
9. has_opposition            4%
10. cpc_density              4%
```

---

## 4. Data Preparation

### 4.1 Training Data Specification

**Dataset Size:**

- Training: 50,000 patents (2010-2016 filings)
- Validation: 10,000 patents (2017-2018 filings)

**Timeline:**

```
2015 filing example:
├─ 2015 ─┬─ 2016 ─┬─ 2017 ─┬─ 2018 ────┬─ 2019 ─┬─ 2020 ─┬─ 2021 ─┤
│ File   │        │        │ Observe   │        │        │ Target  │
│        │        │        │ Features  │        │        │ End     │
└────────┴────────┴────────┴───────────┴────────┴────────┴─────────┘
          ← 3 years →       ← Target: 3 years →
```

### 4.2 Data Extraction

```python
def extract_training_data(
    filing_year_start: int,
    filing_year_end: int,
    observation_offset: int = 3,
    target_offset: int = 3
) -> pd.DataFrame:
    """Extract training data from Parquet"""
    
    patents_df = pl.read_parquet('data/processed/patents.parquet')
    citations_df = pl.read_parquet('data/processed/citations.parquet')
    
    patents = patents_df.filter(
        (pl.col('filing_year') >= filing_year_start) &
        (pl.col('filing_year') <= filing_year_end)
    )
    
    training_data = []
    
    for patent in patents.iter_rows(named=True):
        filing_year = patent['filing_year']
        observation_year = filing_year + observation_offset
        target_year_start = observation_year
        target_year_end = observation_year + target_offset
        
        # Extract features (as of observation year)
        features = extract_features_at_time(patent, observation_year)
        
        # Extract target (citations in target window)
        target = count_citations_in_window(
            patent['patent_id'],
            target_year_start,
            target_year_end,
            citations_df
        )
        
        row = {**features, 'target_citations': target}
        training_data.append(row)
    
    return pd.DataFrame(training_data)
```

### 4.3 Data Quality Checks

```python
def validate_training_data(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport()
    
    # No NULL targets
    null_targets = df['target_citations'].isnull().sum()
    if null_targets > 0:
        report.add_error(f"{null_targets} NULL targets found")
    
    # Feature completeness
    for col in df.columns:
        if col == 'target_citations':
            continue
        null_pct = df[col].isnull().sum() / len(df) * 100
        if null_pct > 20:
            report.add_error(f"{col} has {null_pct:.1f}% NULL")
        elif null_pct > 5:
            report.add_warning(f"{col} has {null_pct:.1f}% NULL")
    
    # No negative targets
    if (df['target_citations'] < 0).sum() > 0:
        report.add_error("Negative targets detected")
    
    # Distribution sanity
    mean_target = df['target_citations'].mean()
    if mean_target < 1 or mean_target > 50:
        report.add_warning(f"Unusual mean target: {mean_target:.1f}")
    
    return report
```

**Acceptance Criteria:**

- Zero NULL targets (CRITICAL)
- <5% NULL in any feature (TARGET)
- Mean target 5-25 citations (SANITY)
- No negative targets (CRITICAL)

---

## 5. Model Training

### 5.1 Model Selection: LightGBM

**Why LightGBM:**

- ✅ Fast (10-100x faster than sklearn)
- ✅ Accurate (state-of-art for tabular data)
- ✅ SHAP compatible (native explainability)
- ✅ Handles missing values
- ✅ Production ready

### 5.2 Hyperparameters

```python
import lightgbm as lgb

params = {
    # Model type
    'objective': 'poisson',      # Poisson regression for count data
    'metric': 'rmse',            # Optimize RMSE
    'boosting_type': 'gbdt',     # Gradient boosting
    
    # Tree structure
    'num_leaves': 31,            # 2^5 - 1
    'max_depth': 8,              # Prevent overfitting
    'min_data_in_leaf': 20,      # Minimum samples per leaf
    
    # Learning
    'learning_rate': 0.05,       # Slower = better generalization
    'num_iterations': 500,       # Boosting rounds
    'early_stopping_rounds': 50, # Stop if no improvement
    
    # Regularization
    'lambda_l1': 0.1,            # L1 regularization
    'lambda_l2': 0.1,            # L2 regularization
    'feature_fraction': 0.8,     # 80% features per tree
    'bagging_fraction': 0.8,     # 80% data per tree
    'bagging_freq': 5,
    
    # Performance
    'num_threads': 4,
    'verbose': 1
}
```

### 5.3 Training Procedure

```python
def train_citation_model(train_df: pd.DataFrame,
                        valid_df: pd.DataFrame,
                        params: dict) -> Tuple[lgb.Booster, dict]:
    """Train LightGBM model"""
    
    # Separate features and target
    feature_cols = [c for c in train_df.columns if c != 'target_citations']
    
    X_train = train_df[feature_cols].values
    y_train = train_df['target_citations'].values
    
    X_valid = valid_df[feature_cols].values
    y_valid = valid_df['target_citations'].values
    
    # Create LightGBM datasets
    train_data = lgb.Dataset(
        X_train,
        label=y_train,
        feature_name=feature_cols
    )
    
    valid_data = lgb.Dataset(
        X_valid,
        label=y_valid,
        reference=train_data
    )
    
    # Train
    logger.info("Training started")
    start_time = time.time()
    
    model = lgb.train(
        params,
        train_data,
        valid_sets=[train_data, valid_data],
        valid_names=['train', 'valid'],
        callbacks=[
            lgb.log_evaluation(period=50),
            lgb.early_stopping(stopping_rounds=50)
        ]
    )
    
    training_time = time.time() - start_time
    
    logger.info(
        "Training completed",
        training_time_sec=training_time,
        num_trees=model.num_trees()
    )
    
    # Compute metrics
    metrics = compute_metrics(model, X_valid, y_valid)
    
    return model, metrics
```

### 5.4 Expected Training Output

```
[50]    train's rmse: 4.23    valid's rmse: 4.67
[100]   train's rmse: 3.89    valid's rmse: 4.52
[150]   train's rmse: 3.62    valid's rmse: 4.45
[200]   train's rmse: 3.41    valid's rmse: 4.42
[250]   train's rmse: 3.25    valid's rmse: 4.41
[300]   train's rmse: 3.12    valid's rmse: 4.40  ← Best
Early stopping at iteration 350

Validation Metrics:
├─ R² Score:      0.68  ✅ (target: >0.65)
├─ RMSE:          4.40  ✅ (target: <4.50)
├─ MAE:           2.87  ✅ (target: <3.00)
└─ Accuracy@3:    72.3% ✅ (target: >70%)
```

---

## 6. Model Validation

### 6.1 Three-Level Validation

**Level 1: Statistical Validation**

- R² > 0.65
- RMSE < 4.5
- Accuracy@3 > 70%

**Level 2: Temporal Holdout**

- Train: 2010-2014 filings
- Test: 2015-2016 filings
- Verify generalization to future

**Level 3: Business Logic**

- Feature importance makes sense
- No negative predictions
- Outliers explainable

### 6.2 Feature Importance Validation

```python
def validate_feature_importance(model: lgb.Booster) -> bool:
    """Validate features make business sense"""
    
    importance = model.feature_importance(importance_type='gain')
    feature_names = model.feature_name()
    
    sorted_idx = np.argsort(importance)[::-1]
    top_features = [feature_names[i] for i in sorted_idx[:10]]
    
    # Check: Recent citations should be top
    if 'citations_year3' not in top_features[:3]:
        logger.warning("citations_year3 not in top 3 - unexpected")
        return False
    
    # Check: Top 10 should be >60% of total
    total_importance = importance.sum()
    top_10_importance = sum(importance[sorted_idx[:10]])
    top_10_pct = top_10_importance / total_importance * 100
    
    if top_10_pct < 60:
        logger.warning(f"Top 10 only {top_10_pct:.1f}% - too diffuse")
        return False
    
    # Check: No single feature dominates
    max_pct = importance[sorted_idx[0]] / total_importance * 100
    if max_pct > 40:
        logger.warning(f"Top feature {max_pct:.1f}% - overfitting risk")
        return False
    
    return True
```

---

## 7. Model Deployment

### 7.1 Model Serialization

```python
# Save model
model.save_model('models/citation_predictor/v1.0/model.txt')

# Save feature names
with open('models/citation_predictor/v1.0/features.json', 'w') as f:
    json.dump(feature_cols, f)

# Save metadata
metadata = {
    'version': '1.0',
    'training_date': datetime.now().isoformat(),
    'training_samples': len(train_df),
    'validation_r2': metrics['r2_score'],
    'hyperparameters': params
}
with open('models/citation_predictor/v1.0/metadata.json', 'w') as f:
    json.dump(metadata, f)
```

### 7.2 Model Loading

```python
class CitationPredictor:
    """Production model wrapper"""
    
    def __init__(self, model_path: str):
        self.model = lgb.Booster(model_file=model_path)
        
        # Load feature names
        with open(model_path.replace('model.txt', 'features.json')) as f:
            self.feature_names = json.load(f)
        
        # Load metadata
        with open(model_path.replace('model.txt', 'metadata.json')) as f:
            self.metadata = json.load(f)
    
    def predict(self, features: dict) -> float:
        """Predict citations for single patent"""
        
        # Validate features
        missing = set(self.feature_names) - set(features.keys())
        if missing:
            raise ValueError(f"Missing features: {missing}")
        
        # Order features correctly
        X = np.array([[features[f] for f in self.feature_names]])
        
        # Predict
        prediction = self.model.predict(X)[0]
        
        return max(0, prediction)  # Ensure non-negative
```

### 7.3 Inference Performance

**Target:** <100ms per prediction

**Optimization:**

```python
# Batch prediction (faster)
def predict_batch(self, features_list: List[dict]) -> List[float]:
    X = np.array([
        [f[name] for name in self.feature_names]
        for f in features_list
    ])
    
    predictions = self.model.predict(X)
    return [max(0, p) for p in predictions]
```

---

## 8. Explainability & SHAP

### 8.1 SHAP Overview

**SHAP (SHapley Additive exPlanations):**

- Explains each prediction
- Shows which features contributed how much
- Mathematically grounded (game theory)

### 8.2 SHAP Training

```python
import shap

# Create explainer
explainer = shap.TreeExplainer(model)

# Save explainer
with open('models/citation_predictor/v1.0/explainer.pkl', 'wb') as f:
    pickle.dump(explainer, f)
```

### 8.3 SHAP Inference

```python
def explain_prediction(self, features: dict) -> dict:
    """Explain prediction with SHAP"""
    
    # Predict
    X = np.array([[features[f] for f in self.feature_names]])
    prediction = self.model.predict(X)[0]
    
    # SHAP values
    shap_values = self.explainer.shap_values(X)[0]
    
    # Get top 3 drivers
    abs_shap = np.abs(shap_values)
    top_idx = np.argsort(abs_shap)[::-1][:3]
    
    drivers = []
    for idx in top_idx:
        feature_name = self.feature_names[idx]
        impact = shap_values[idx]
        drivers.append({
            'feature': feature_name,
            'impact': float(impact),
            'description': self._describe_feature(feature_name, impact)
        })
    
    return {
        'prediction': float(prediction),
        'drivers': drivers
    }

def _describe_feature(self, feature: str, impact: float) -> str:
    """Human-readable feature description"""
    
    descriptions = {
        'citation_velocity': 'Strong citation growth trend' if impact > 0 else 'Slow citation growth',
        'market_growth_rate': 'Hot market driving citations' if impact > 0 else 'Declining market',
        'is_granted': 'Granted patent attracts citations' if impact > 0 else 'Not yet granted',
        # ... more descriptions
    }
    
    return descriptions.get(feature, feature)
```

### 8.4 Example SHAP Output

```json
{
  "prediction": 18.3,
  "drivers": [
    {
      "feature": "citation_velocity",
      "impact": 6.2,
      "description": "Strong citation growth trend"
    },
    {
      "feature": "market_growth_rate",
      "impact": 3.8,
      "description": "Hot market driving citations"
    },
    {
      "feature": "opposition_survived",
      "impact": 2.4,
      "description": "Quality signal attracts citations"
    }
  ]
}
```

---

## 9. Fallback Strategies

### 9.1 When ML Fails

**Fallback Hierarchy:**

```
1. Try ML model
   ↓ fails
2. Try simple linear trend
   ↓ fails
3. Use field average
```

### 9.2 Linear Trend Fallback

```python
def predict_with_linear_fallback(self, patent: Patent) -> dict:
    """Predict with fallback to linear trend"""
    
    try:
        # Try ML model
        features = self.feature_engineer.create_features(patent)
        prediction = self.model.predict(features)
        
        return {
            'prediction': prediction,
            'method': 'ML',
            'confidence': 'HIGH'
        }
    
    except Exception as e:
        logger.warning("ML prediction failed, using linear fallback", error=str(e))
        
        # Fallback: Linear trend
        historical_citations = [
            patent.citations_year1,
            patent.citations_year2,
            patent.citations_year3
        ]
        
        # Simple linear regression
        slope = (historical_citations[-1] - historical_citations[0]) / 2
        prediction = max(0, historical_citations[-1] + slope * 3)
        
        return {
            'prediction': prediction,
            'method': 'LINEAR_TREND',
            'confidence': 'LOW'
        }
```

### 9.3 Field Average Fallback

```python
def predict_with_field_average(self, patent: Patent) -> dict:
    """Ultimate fallback: field average"""
    
    # Field averages (pre-computed)
    FIELD_AVERAGES_3YR = {
        'A': 11.2,
        'B': 12.8,
        'C': 9.5,
        'G': 14.3,
        'H': 15.7
    }
    
    prediction = FIELD_AVERAGES_3YR.get(patent.cpc_section, 12.0)
    
    return {
        'prediction': prediction,
        'method': 'FIELD_AVERAGE',
        'confidence': 'LOW'
    }
```

---

## 10. Monitoring & Maintenance

### 10.1 Production Metrics

**Track:**

- Prediction latency (p50, p95, p99)
- Prediction errors (when actual known)
- SHAP computation time
- Model cache hit rate

```python
class ModelMonitoring:
    """Monitor ML model in production"""
    
    def __init__(self):
        self.predictions_made = 0
        self.total_latency_ms = 0
        self.errors = []
    
    def record_prediction(self, latency_ms: float, prediction: float):
        self.predictions_made += 1
        self.total_latency_ms += latency_ms
        
        metrics.record_timing('ml_prediction', latency_ms)
        metrics.increment('ml_predictions_total')
    
    def record_error(self, error_type: str, details: str):
        self.errors.append({
            'type': error_type,
            'details': details,
            'timestamp': datetime.now()
        })
        
        metrics.increment('ml_errors_total', labels={'type': error_type})
    
    def get_report(self) -> dict:
        return {
            'predictions_made': self.predictions_made,
            'avg_latency_ms': self.total_latency_ms / self.predictions_made if self.predictions_made > 0 else 0,
            'error_count': len(self.errors),
            'recent_errors': self.errors[-10:]
        }
```

### 10.2 Model Retraining

**When to Retrain:**

- Every 6 months (scheduled)
- When validation R² drops below 0.55
- When new data patterns emerge

**Retraining Procedure:**

1. Extract new training data
2. Validate data quality
3. Train new model
4. Validate against holdout
5. A/B test (10% traffic)
6. Full rollout if successful

---

## Summary

This ML Guidelines PRD defines:

✅ **ML problem** (Poisson regression, 3-year prediction)  
✅ **Features** (42 features across 8 categories)  
✅ **Data preparation** (temporal split, quality checks)  
✅ **Training** (LightGBM with hyperparameters)  
✅ **Validation** (3-level: statistical, temporal, business)  
✅ **Deployment** (serialization, loading, inference)  
✅ **Explainability** (SHAP for every prediction)  
✅ **Fallbacks** (linear trend → field average)  
✅ **Monitoring** (latency, errors, retraining triggers)

**Key Decisions:**

- LightGBM over alternatives (fast, accurate, explainable)
- Poisson objective (count data distribution)
- Temporal validation (no future leakage)
- SHAP explainability (trust through transparency)
- Graceful degradation (fallback strategies)

**Related Documents:**

- [[02-Education#7]] - ML concepts explained
- [[PRD-Data-Requirements#3-4]] - ML feature data requirements
- [[PRD-Service-Layers#4]] - Engine implementation patterns

**Next Steps:**

1. Extract training data (Week 5)
2. Engineer features (Week 5)
3. Train model (Week 6)
4. Validate (Week 6)
5. Deploy (Week 7)
6. Monitor (ongoing)

---

**Document Owner:** ML Engineer (Developer 3)  
**Last Reviewed:** December 2024  
**Next Review:** After model training (Week 6)