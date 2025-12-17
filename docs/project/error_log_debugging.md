# PRD: Error Logging & Debugging Standards

**Document Version:** 1.0  
**Last Updated:** December 2024  
**Status:** Approved for Implementation  
**Related Documents:** [[PRD-Service-Layers]], [[PRD-Architecture]], [[PRD-Testing-Strategy]]

---

## Table of Contents

1. [Overview](#1-overview)
2. [Logging Philosophy](#2-logging-philosophy)
3. [Log Levels & Usage](#3-log-levels--usage)
4. [Structured Logging](#4-structured-logging)
5. [Error Handling Patterns](#5-error-handling-patterns)
6. [Exception Hierarchy](#6-exception-hierarchy)
7. [Debugging Guidelines](#7-debugging-guidelines)
8. [Monitoring & Alerting](#8-monitoring--alerting)
9. [Log Analysis](#9-log-analysis)
10. [Production Debugging](#10-production-debugging)

---

## 1. Overview

### 1.1 Purpose

This document defines **comprehensive logging and error handling standards** for PatentIQ. Think of it as the **diagnostic manual** that enables quick debugging and issue resolution.

**Analogy:** Just as a car's diagnostic system logs error codes and sensor data (helping mechanics quickly identify problems), our logging system captures structured events and errors that enable developers to quickly diagnose and fix issues.

### 1.2 Logging Goals

**Goal 1: Observability**

Every request should be traceable from entry to exit.

```
User Request → API → Orchestrator → Engines → Repository → Data Source
     ↓           ↓         ↓            ↓           ↓            ↓
  Log Entry   Log Rcvd  Log Start   Log Calc    Log Query   Log Result
```

**Goal 2: Debuggability**

Logs should contain enough context to reproduce and fix issues.

**Goal 3: Performance Monitoring**

Logs should capture timing information for optimization.

**Goal 4: Security Auditing**

Logs should track access patterns and potential security issues.

### 1.3 Logging Principles

**Principle 1: Log Events, Not Messages**

```python
# ❌ Bad: Generic message
logger.info("Processing patent")

# ✅ Good: Structured event
logger.info("patent_analysis_started", patent_id="EP1234567B1", user_id="user_123")
```

**Principle 2: Include Context**

Every log should answer: Who? What? When? Where? Why?

**Principle 3: Be Consistent**

Use same event names and field names throughout codebase.

**Principle 4: No Sensitive Data**

Never log passwords, API keys, personal information.

---

## 2. Logging Philosophy

### 2.1 Structured vs. Unstructured

**Unstructured Logging (Old Way):**
```python
logger.info("User john@example.com analyzed patent EP1234567B1 in 2.3 seconds")
```

**Problems:**
- Hard to parse programmatically
- Inconsistent format
- Can't easily query "all requests > 2 seconds"

**Structured Logging (Our Way):**
```python
logger.info(
    "patent_analysis_completed",
    user_email="john@example.com",
    patent_id="EP1234567B1",
    duration_ms=2300
)
```

**Benefits:**
- Easy to parse (JSON format)
- Consistent structure
- Queryable: `SELECT * FROM logs WHERE duration_ms > 2000`
- Indexable for fast search

### 2.2 Log as Data

**Think of logs as structured database records:**

```json
{
  "timestamp": "2024-12-15T14:32:18.234Z",
  "level": "INFO",
  "event": "patent_analysis_completed",
  "patent_id": "EP1234567B1",
  "user_id": "user_123",
  "duration_ms": 2300,
  "category": "HIDDEN_GEM",
  "service": "analysis_orchestrator",
  "trace_id": "abc123"
}
```

This enables:
- Filtering: Show me all HIDDEN_GEM patents
- Aggregation: Average duration by category
- Correlation: Link all logs for trace_id abc123
- Alerting: Alert if duration_ms > 5000

---

## 3. Log Levels & Usage

### 3.1 Five Standard Levels

| Level | When to Use | Examples | Action Required |
|-------|-------------|----------|-----------------|
| **DEBUG** | Development details | Cache lookup, SQL query | None (filtered in prod) |
| **INFO** | Normal operations | Request received, analysis completed | None (monitoring) |
| **WARNING** | Unexpected but handled | Low data quality, cache miss | Review periodically |
| **ERROR** | Error occurred but recovered | API timeout (retried), validation failed | Investigate same day |
| **CRITICAL** | System failure | Database down, model missing | **IMMEDIATE ACTION** |

### 3.2 DEBUG Level

**Use for:** Development and troubleshooting

```python
logger.debug(
    "cache_lookup",
    cache_key="patent:EP1234567B1",
    cache_tier="redis",
    ttl_seconds=86400
)

logger.debug(
    "sql_query_executed",
    query="SELECT * FROM patents WHERE id = ?",
    params=["EP1234567B1"],
    rows_returned=1,
    duration_ms=45
)

logger.debug(
    "feature_engineering",
    patent_id="EP1234567B1",
    features_created=42,
    missing_features=["claim_count"]
)
```

**Configuration:**
- Enabled: Development only
- Disabled: Production (too verbose)
- Can be enabled temporarily for specific debugging

### 3.3 INFO Level

**Use for:** Normal operations that should be recorded

```python
logger.info(
    "api_request_received",
    endpoint="/api/v1/analyze",
    method="POST",
    patent_id="EP1234567B1",
    user_id="user_123",
    client_ip="192.168.1.100"
)

logger.info(
    "patent_analysis_started",
    patent_id="EP1234567B1",
    dimensions=["influence", "legal", "financial", "future"]
)

logger.info(
    "patent_analysis_completed",
    patent_id="EP1234567B1",
    duration_ms=2300,
    category="HIDDEN_GEM",
    scores={
        "influence": 48,
        "legal": 98,
        "financial": 91,
        "future": 76
    }
)

logger.info(
    "ml_prediction_made",
    patent_id="EP1234567B1",
    predicted_citations=18,
    confidence="HIGH",
    method="lightgbm",
    model_version="v1.0"
)
```

### 3.4 WARNING Level

**Use for:** Unexpected situations that were handled

```python
logger.warning(
    "low_data_quality",
    patent_id="EP1234567B1",
    missing_fields=["claim_count", "opposition_data"],
    completeness_score=0.65,
    impact="Reduced confidence to MEDIUM"
)

logger.warning(
    "cache_miss_high_frequency",
    cache_key_pattern="patent:*",
    miss_rate=0.75,
    expected_rate=0.40,
    recommendation="Consider increasing cache TTL"
)

logger.warning(
    "slow_query",
    query_type="citation_lookup",
    patent_id="EP1234567B1",
    duration_ms=3500,
    threshold_ms=1000,
    suggestion="Add index on citing_patent_id"
)

logger.warning(
    "ml_fallback_used",
    patent_id="EP1234567B1",
    reason="Model prediction failed",
    fallback_method="linear_trend",
    confidence_degraded_to="LOW"
)
```

### 3.5 ERROR Level

**Use for:** Errors that require attention

```python
logger.error(
    "patent_not_found",
    patent_id="EP9999999B1",
    user_id="user_123",
    searched_in=["parquet", "cache"],
    suggestion="Verify patent number format"
)

logger.error(
    "calculation_failed",
    dimension="influence",
    patent_id="EP1234567B1",
    error_type="DivisionByZero",
    error_message="Patent age is zero",
    stack_trace=traceback.format_exc()
)

logger.error(
    "external_api_timeout",
    service="epo_register",
    patent_id="EP1234567B1",
    timeout_seconds=30,
    retry_count=3,
    fallback_used=True
)

logger.error(
    "data_validation_failed",
    stage="feature_engineering",
    patent_id="EP1234567B1",
    validation_errors=[
        "citations_year3 is negative",
        "family_size is zero"
    ]
)
```

### 3.6 CRITICAL Level

**Use for:** System failures requiring immediate action

```python
logger.critical(
    "database_connection_lost",
    database="parquet_lake",
    error="Connection refused",
    impact="All queries failing",
    action_required="IMMEDIATE - Check database service"
)

logger.critical(
    "ml_model_missing",
    model_path="/models/citation_predictor/v1.0/model.txt",
    error="File not found",
    impact="All Future dimension calculations failing",
    fallback="Using linear trend for all predictions"
)

logger.critical(
    "cache_service_down",
    service="redis",
    error="Connection timeout",
    impact="All requests hitting database directly",
    performance_degradation="10x slower"
)

logger.critical(
    "out_of_memory",
    service="analysis_orchestrator",
    memory_used_gb=7.8,
    memory_limit_gb=8.0,
    action="Restarting service"
)
```

---

## 4. Structured Logging

### 4.1 Implementation with Structlog

```python
import structlog

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer()  # Development
        # structlog.processors.JSONRenderer()  # Production
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True
)

# Get logger
logger = structlog.get_logger(__name__)
```

### 4.2 Standard Fields

**Every log should include:**

```python
logger.info(
    "event_name",           # REQUIRED: What happened
    # Context fields
    service="service_name", # Which service
    user_id="user_123",     # Who
    patent_id="EP1234567B1",# What entity
    # Timing
    duration_ms=2300,       # How long
    # Result
    status="success",       # Outcome
    # Trace
    trace_id="abc123",      # Request correlation
    span_id="xyz789"        # Span within trace
)
```

### 4.3 Context Binding

**Bind context once, use everywhere:**

```python
# At request entry, bind common context
logger = logger.bind(
    trace_id=request_id,
    user_id=user.id,
    service="analysis_orchestrator"
)

# Now all logs include this context automatically
logger.info("request_started")  # Includes trace_id, user_id, service

# Do work...

logger.info("request_completed", duration_ms=2300)  # Still includes context
```

### 4.4 Standard Event Names

**Naming Convention:** `{component}_{action}_{status}`

```python
# Component: What part of system
# Action: What it's doing
# Status: started/completed/failed

"api_request_received"
"patent_analysis_started"
"patent_analysis_completed"
"patent_analysis_failed"

"cache_lookup_hit"
"cache_lookup_miss"

"ml_prediction_started"
"ml_prediction_completed"
"ml_prediction_failed"

"database_query_started"
"database_query_completed"
"database_query_timeout"
```

---

## 5. Error Handling Patterns

### 5.1 Try-Except-Log Pattern

```python
def calculate_influence(self, patent: Patent) -> InfluenceScore:
    """Calculate influence with proper error handling"""
    
    logger = logger.bind(patent_id=patent.id, dimension="influence")
    
    try:
        logger.info("influence_calculation_started")
        
        # Main calculation
        score = self._calculate_score(patent)
        
        logger.info(
            "influence_calculation_completed",
            score=score.value,
            confidence=score.confidence,
            duration_ms=elapsed_ms
        )
        
        return score
        
    except InsufficientDataError as e:
        logger.warning(
            "influence_calculation_degraded",
            reason="insufficient_data",
            missing_fields=e.missing_fields,
            fallback="using_baseline_score"
        )
        return self._fallback_score(patent)
        
    except Exception as e:
        logger.error(
            "influence_calculation_failed",
            error_type=type(e).__name__,
            error_message=str(e),
            stack_trace=traceback.format_exc()
        )
        raise
```

### 5.2 Context Manager Pattern

```python
from contextlib import contextmanager
import time

@contextmanager
def log_operation(logger, operation: str, **context):
    """Context manager for automatic operation logging"""
    
    start_time = time.time()
    
    logger.info(f"{operation}_started", **context)
    
    try:
        yield
        
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"{operation}_completed",
            duration_ms=duration_ms,
            **context
        )
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            f"{operation}_failed",
            duration_ms=duration_ms,
            error_type=type(e).__name__,
            error_message=str(e),
            **context
        )
        raise

# Usage
with log_operation(logger, "patent_analysis", patent_id=patent.id):
    result = orchestrator.analyze(patent)
```

### 5.3 Decorator Pattern

```python
from functools import wraps

def log_function(logger):
    """Decorator to automatically log function entry/exit"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract identifiable info from args
            func_name = func.__name__
            
            logger.info(
                f"function_called",
                function=func_name,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"function_completed",
                    function=func_name,
                    duration_ms=duration_ms
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"function_failed",
                    function=func_name,
                    duration_ms=duration_ms,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                raise
        
        return wrapper
    return decorator

# Usage
@log_function(logger)
def calculate_influence(patent: Patent) -> InfluenceScore:
    # Function automatically logged
    return score
```

---

## 6. Exception Hierarchy

### 6.1 Custom Exception Classes

```python
class PatentIQException(Exception):
    """Base exception for all PatentIQ errors"""
    
    def __init__(self, message: str, **context):
        super().__init__(message)
        self.message = message
        self.context = context
    
    def to_dict(self) -> dict:
        """Convert exception to loggable dict"""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            **self.context
        }

# Data-related exceptions
class DataError(PatentIQException):
    """Base class for data errors"""
    pass

class PatentNotFoundError(DataError):
    """Patent doesn't exist in database"""
    pass

class InsufficientDataError(DataError):
    """Patent lacks required data for calculation"""
    
    def __init__(self, message: str, missing_fields: List[str], **context):
        super().__init__(message, missing_fields=missing_fields, **context)
        self.missing_fields = missing_fields

# Calculation-related exceptions
class CalculationError(PatentIQException):
    """Base class for calculation errors"""
    pass

class DimensionCalculationError(CalculationError):
    """Error calculating specific dimension"""
    
    def __init__(self, dimension: str, message: str, **context):
        super().__init__(message, dimension=dimension, **context)
        self.dimension = dimension

# External service exceptions
class ExternalServiceError(PatentIQException):
    """Base class for external service errors"""
    pass

class MLModelError(ExternalServiceError):
    """ML model prediction failed"""
    pass

class CacheServiceError(ExternalServiceError):
    """Cache service unavailable"""
    pass
```

### 6.2 Using Custom Exceptions

```python
def get_patent(self, patent_id: str) -> Patent:
    """Retrieve patent with proper exception handling"""
    
    patent = self._query_parquet(patent_id)
    
    if not patent:
        raise PatentNotFoundError(
            f"Patent {patent_id} not found",
            patent_id=patent_id,
            searched_locations=["parquet", "cache"]
        )
    
    # Validate data completeness
    missing_fields = self._check_required_fields(patent)
    
    if missing_fields:
        raise InsufficientDataError(
            f"Patent {patent_id} missing required fields",
            patent_id=patent_id,
            missing_fields=missing_fields,
            completeness_score=self._calculate_completeness(patent)
        )
    
    return patent

# Caller handles exceptions
try:
    patent = patent_repo.get_patent("EP1234567B1")
except PatentNotFoundError as e:
    logger.error("patent_retrieval_failed", **e.to_dict())
    raise HTTPException(status_code=404, detail=e.message)
except InsufficientDataError as e:
    logger.warning("patent_data_incomplete", **e.to_dict())
    # Continue with degraded analysis
```

---

## 7. Debugging Guidelines

### 7.1 Trace ID Propagation

**Every request gets unique trace ID:**

```python
import uuid

class RequestContext:
    """Thread-local request context"""
    
    def __init__(self):
        self.trace_id = str(uuid.uuid4())
        self.user_id = None
        self.start_time = time.time()

# FastAPI middleware
@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    # Generate or extract trace ID
    trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4()))
    
    # Bind to logger
    logger = structlog.get_logger().bind(trace_id=trace_id)
    
    # Store in request state
    request.state.trace_id = trace_id
    request.state.logger = logger
    
    response = await call_next(request)
    
    # Add trace ID to response headers
    response.headers['X-Trace-ID'] = trace_id
    
    return response
```

**Now all logs for a request share trace_id:**

```
[2024-12-15 14:32:18] INFO trace_id=abc-123 event=request_received
[2024-12-15 14:32:18] INFO trace_id=abc-123 event=patent_analysis_started
[2024-12-15 14:32:19] INFO trace_id=abc-123 event=influence_calculation_completed
[2024-12-15 14:32:19] INFO trace_id=abc-123 event=legal_calculation_completed
[2024-12-15 14:32:20] INFO trace_id=abc-123 event=patent_analysis_completed
```

**Query logs by trace_id to see entire request flow:**

```bash
grep "trace_id=abc-123" application.log
```

### 7.2 Performance Profiling

**Add timing to critical sections:**

```python
class PerformanceLogger:
    """Log performance metrics"""
    
    def __init__(self, logger):
        self.logger = logger
        self.timings = {}
    
    @contextmanager
    def time_section(self, section_name: str):
        """Time a code section"""
        start = time.time()
        yield
        elapsed_ms = (time.time() - start) * 1000
        
        self.timings[section_name] = elapsed_ms
        
        self.logger.debug(
            "section_timed",
            section=section_name,
            duration_ms=elapsed_ms
        )
    
    def log_summary(self):
        """Log performance summary"""
        total_ms = sum(self.timings.values())
        
        self.logger.info(
            "performance_summary",
            total_duration_ms=total_ms,
            breakdown=self.timings,
            slowest_section=max(self.timings, key=self.timings.get)
        )

# Usage
perf = PerformanceLogger(logger)

with perf.time_section("retrieve_patent"):
    patent = patent_repo.get_by_id(patent_id)

with perf.time_section("calculate_dimensions"):
    scores = await orchestrator.calculate_dimensions(patent)

with perf.time_section("synthesize_category"):
    category = synthesis_engine.categorize(scores)

perf.log_summary()
# Logs: total=2300ms, breakdown={retrieve:45ms, calculate:2100ms, synthesize:155ms}
```

### 7.3 Data Snapshots

**Log data state at key points:**

```python
def calculate_influence(self, patent: Patent) -> InfluenceScore:
    """Calculate with data snapshots for debugging"""
    
    # Log input state
    logger.debug(
        "influence_input_data",
        patent_id=patent.id,
        forward_citations=patent.forward_citations,
        backward_citations=patent.backward_citations,
        age_years=patent.age_years,
        cpc_section=patent.cpc_section
    )
    
    # Calculate components
    velocity = self._calculate_velocity(patent.forward_citations, patent.age_years)
    field_normalized = self._calculate_field_normalized(patent.forward_citations, patent.cpc_section)
    
    # Log intermediate state
    logger.debug(
        "influence_components",
        patent_id=patent.id,
        velocity=velocity,
        field_normalized=field_normalized
    )
    
    # Synthesize
    final_score = self._synthesize(velocity, field_normalized)
    
    # Log output state
    logger.debug(
        "influence_output_data",
        patent_id=patent.id,
        final_score=final_score
    )
    
    return InfluenceScore(value=final_score)
```

---

## 8. Monitoring & Alerting

### 8.1 Key Metrics to Monitor

```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
requests_total = Counter(
    'patentiq_requests_total',
    'Total requests',
    ['endpoint', 'status']
)

request_duration = Histogram(
    'patentiq_request_duration_seconds',
    'Request duration',
    ['endpoint']
)

# Error metrics
errors_total = Counter(
    'patentiq_errors_total',
    'Total errors',
    ['error_type', 'service']
)

# System metrics
active_requests = Gauge(
    'patentiq_active_requests',
    'Currently active requests'
)

cache_hit_rate = Gauge(
    'patentiq_cache_hit_rate',
    'Cache hit rate percentage'
)
```

### 8.2 Alert Conditions

```yaml
# Alert definitions
alerts:
  - name: HighErrorRate
    condition: errors_total / requests_total > 0.05
    duration: 5m
    severity: HIGH
    action: page_oncall
    message: "Error rate above 5% for 5 minutes"
  
  - name: SlowRequests
    condition: request_duration_p95 > 5s
    duration: 10m
    severity: MEDIUM
    action: slack_alert
    message: "95th percentile latency above 5s"
  
  - name: CacheDown
    condition: cache_hit_rate < 0.20
    duration: 5m
    severity: HIGH
    action: page_oncall
    message: "Cache hit rate below 20% - possible Redis issue"
  
  - name: MLModelErrors
    condition: increase(errors_total{error_type="MLModelError"}[5m]) > 10
    severity: HIGH
    action: page_oncall
    message: "ML model failing repeatedly"
```

### 8.3 Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    """System health check"""
    
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Check database
    try:
        patent_repo.get_by_id("EP1234567B1")
        health["checks"]["database"] = "healthy"
    except Exception as e:
        health["checks"]["database"] = "unhealthy"
        health["status"] = "degraded"
        logger.error("health_check_database_failed", error=str(e))
    
    # Check cache
    try:
        cache.get("health_check_key")
        health["checks"]["cache"] = "healthy"
    except Exception as e:
        health["checks"]["cache"] = "unhealthy"
        health["status"] = "degraded"
        logger.error("health_check_cache_failed", error=str(e))
    
    # Check ML model
    try:
        ml_predictor.predict({"citations_year3": 10, ...})
        health["checks"]["ml_model"] = "healthy"
    except Exception as e:
        health["checks"]["ml_model"] = "unhealthy"
        health["status"] = "degraded"
        logger.error("health_check_ml_failed", error=str(e))
    
    return health
```

---

## 9. Log Analysis

### 9.1 Common Queries

**Find all errors for a patent:**
```bash
grep "patent_id=EP1234567B1" application.log | grep "level=ERROR"
```

**Find slow requests (>5s):**
```bash
jq 'select(.duration_ms > 5000)' application.log
```

**Count errors by type:**
```bash
jq -r '.error_type' application.log | sort | uniq -c | sort -rn
```

**Average duration by endpoint:**
```bash
jq -r 'select(.event=="request_completed") | "\(.endpoint) \(.duration_ms)"' application.log | \
  awk '{sum[$1]+=$2; count[$1]++} END {for(e in sum) print e, sum[e]/count[e]}'
```

### 9.2 Log Aggregation

**Using ELK Stack (Elasticsearch, Logstash, Kibana):**

```python
# Configure Logstash output
import logging
from logstash_async.handler import AsynchronousLogstashHandler

handler = AsynchronousLogstashHandler(
    host='logstash.example.com',
    port=5959,
    database_path='logstash.db'
)

logger.addHandler(handler)
```

**Kibana Queries:**
```
# All errors in last hour
level:ERROR AND @timestamp:[now-1h TO now]

# Slow requests
duration_ms:>5000

# Specific patent's journey
trace_id:"abc-123"
```

---

## 10. Production Debugging

### 10.1 Debug Mode

**Enable debug logging for specific requests:**

```python
@app.middleware("http")
async def debug_mode(request: Request, call_next):
    # Check for debug header
    if request.headers.get('X-Debug-Mode') == 'true':
        # Temporarily enable DEBUG level
        logger.level = logging.DEBUG
        logger.info("debug_mode_enabled", trace_id=request.state.trace_id)
    
    response = await call_next(request)
    
    # Reset log level
    logger.level = logging.INFO
    
    return response
```

**Usage:**
```bash
curl -H "X-Debug-Mode: true" http://api.patentiq.com/analyze/EP1234567B1
```

### 10.2 Reproduce Issues

**Log enough context to reproduce:**

```python
logger.error(
    "calculation_failed",
    # Input state
    patent_id=patent.id,
    patent_data=patent.to_dict(),  # Full patent data
    # Configuration
    model_version=config.ml_model_version,
    cache_enabled=config.cache_enabled,
    # Error details
    error_type=type(e).__name__,
    error_message=str(e),
    stack_trace=traceback.format_exc(),
    # Reproduction info
    reproduce_with=f"python debug.py --patent-id {patent.id}"
)
```

### 10.3 Emergency Debugging

**When production is broken:**

1. **Check health endpoint:**
```bash
curl http://api.patentiq.com/health
```

2. **Grep recent CRITICALs:**
```bash
tail -n 1000 application.log | grep "CRITICAL"
```

3. **Check error spike:**
```bash
tail -n 1000 application.log | grep "ERROR" | cut -d' ' -f1 | uniq -c
```

4. **Find common error:**
```bash
tail -n 1000 application.log | grep "ERROR" | jq -r '.error_type' | sort | uniq -c | sort -rn | head -5
```

5. **Check specific service:**
```bash
tail -n 1000 application.log | grep "service=ml_predictor" | grep "ERROR"
```

---

## Summary

This Error Logging PRD defines:

✅ **5 log levels** (DEBUG, INFO, WARNING, ERROR, CRITICAL)  
✅ **Structured logging** (JSON format, queryable)  
✅ **Standard fields** (trace_id, service, duration_ms)  
✅ **Error handling patterns** (try-except-log, context manager, decorator)  
✅ **Exception hierarchy** (custom exceptions with context)  
✅ **Debugging guidelines** (trace ID, performance profiling, data snapshots)  
✅ **Monitoring** (Prometheus metrics, health checks, alerts)  
✅ **Log analysis** (queries, aggregation, Kibana)  
✅ **Production debugging** (debug mode, reproduction, emergency procedures)

**Key Principles:**
- Log events, not messages
- Include context (who, what, when, where)
- Be consistent (standard event names)
- No sensitive data
- Structured format (JSON)

**Related Documents:**
- [[PRD-Service-Layers]] - Service implementation patterns
- [[PRD-Architecture]] - System architecture
- [[PRD-Testing-Strategy]] - Testing approach

**Next Steps:**
1. Configure structlog (Week 1)
2. Define standard event names (Week 1)
3. Implement custom exceptions (Week 2)
4. Add logging to all services (Weeks 2-10)
5. Set up monitoring (Week 11)
6. Configure alerts (Week 11)

---

**Document Owner:** DevOps Lead  
**Last Reviewed:** December 2024  
**Next Review:** Week 6 (after major services implemented)