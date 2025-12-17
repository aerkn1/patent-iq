# PRD: UI/UX Design Specifications

**Document Version:** 1.0  
**Last Updated:** December 2024  
**Status:** Approved for Implementation  
**Related Documents:** [[PRD-Architecture]], [[Use-Cases-Summary]], [[PRD-Service-Layers]]

---

## Table of Contents

1. [Overview](#1-overview)
2. [Design Philosophy](#2-design-philosophy)
3. [Design System](#3-design-system)
4. [Page-by-Page Specifications](#4-page-by-page-specifications)
5. [Component Library](#5-component-library)
6. [Data Visualization](#6-data-visualization)
7. [Responsive Design](#7-responsive-design)
8. [Accessibility](#8-accessibility)
9. [Performance Optimization](#9-performance-optimization)
10. [Risk Mitigation](#10-risk-mitigation)

---

## 1. Overview

### 1.1 Purpose

This document defines **complete UI/UX specifications** for PatentIQ, transforming API responses into an elegant, user-friendly interface that impresses through **simplicity and perfection**, not complexity.

**Design Principle:** "Perfection is achieved not when there is nothing more to add, but when there is nothing left to take away." - Antoine de Saint-Exupéry

**Analogy:** Think of Apple's product design - minimal, clean, but perfectly functional. Every element has a purpose. No decoration for decoration's sake.

### 1.2 Design Goals

**Goal 1: Clarity Over Cleverness**

User should understand the interface immediately without tutorial.

**Goal 2: Data-Driven, Not Decoration-Driven**

Every visual element serves the data, not the designer's portfolio.

**Goal 3: Speed and Responsiveness**

Interface feels instant (<100ms perceived latency).

**Goal 4: Professional, Not Playful**

This is a business tool for IP managers making €100K+ decisions.

### 1.3 Target Users

**Primary User:** IP Portfolio Manager
- Age: 35-55
- Technical literacy: Medium-High
- Domain expertise: High (patents, licensing)
- Usage pattern: Weekly analysis sessions, 2-4 hours
- Key need: Quick decisions backed by data

**Secondary User:** Patent Attorney
- Similar profile
- More legal focus
- Needs citation to source data

**Tertiary User:** C-Level Executive
- Lower technical literacy
- Needs high-level summaries
- Visual learner (charts > tables)

---

## 2. Design Philosophy

### 2.1 Core Principles

**Principle 1: Progressive Disclosure**

Show most important information first, details on demand.

```
Landing → Summary → Details → Raw Data
   ↓         ↓         ↓          ↓
  10s       30s       2min      5min
```

**Principle 2: Consistent Information Architecture**

Same pattern across all pages:
1. Header (context: what am I looking at?)
2. Key metrics (4-6 numbers that matter)
3. Primary visualization (the story)
4. Supporting details (drill-down)
5. Actions (what can I do?)

**Principle 3: Ruthless Prioritization**

If it's not in top 20% of importance, it goes to "Details" section.

**Principle 4: No Chartjunk**

Every pixel serves the data. No:
- Decorative icons
- Unnecessary animations
- 3D effects
- Gradients (unless functional)
- Drop shadows (unless needed for layering)

### 2.2 Visual Language

**Typography:**
```
Headings: Inter (clean, professional)
Body: Inter (same family for consistency)
Monospace: JetBrains Mono (for patent numbers, codes)

Sizes:
- H1: 32px (page title)
- H2: 24px (section title)
- H3: 18px (subsection)
- Body: 16px (readable without zoom)
- Small: 14px (metadata, captions)
```

**Color Palette:**

```
Primary Colors (Data):
- Success: #10B981 (green) - positive metrics
- Warning: #F59E0B (amber) - caution
- Error: #EF4444 (red) - negative metrics
- Info: #3B82F6 (blue) - neutral info

Grayscale (Structure):
- Background: #FFFFFF (white)
- Surface: #F9FAFB (light gray)
- Border: #E5E7EB (medium gray)
- Text Primary: #111827 (near black)
- Text Secondary: #6B7280 (gray)

Category Colors (4D Dimensions):
- Influence: #8B5CF6 (purple)
- Legal: #3B82F6 (blue)
- Financial: #10B981 (green)
- Future: #F59E0B (amber)
```

**Why These Colors:**
- High contrast (WCAG AAA compliant)
- Color-blind friendly (tested)
- Professional (not playful)
- Sufficient variety without chaos

**Spacing:**
```
4px  - Tight (related items)
8px  - Default (comfortable)
16px - Breathing room (sections)
24px - Separation (major sections)
32px - Page margins
```

**Borders & Shadows:**
```
Border: 1px solid #E5E7EB (subtle)
Shadow (cards): 0 1px 3px rgba(0,0,0,0.1) (barely visible)
Shadow (modals): 0 20px 25px rgba(0,0,0,0.15) (obvious layering)
```

### 2.3 Design Anti-Patterns to Avoid

**❌ Don't:**
1. Use more than 3 font sizes on a page
2. Use more than 5 colors on a page (excluding charts)
3. Animate anything that doesn't communicate state change
4. Use icons without labels (except universally understood: ✕, ⚙, 🔍)
5. Hide critical information in tooltips
6. Use acronyms without first defining them
7. Show loading spinners for <500ms operations
8. Use modals for confirmations that aren't destructive
9. Disable buttons without explaining why
10. Use pagination when infinite scroll works better

**✅ Do:**
1. Show loading states for >500ms operations
2. Provide immediate feedback for all actions
3. Explain errors in plain English
4. Show progress for multi-step processes
5. Preserve user state across navigation
6. Provide keyboard shortcuts for power users
7. Make all interactive elements obviously clickable
8. Group related information visually
9. Use whitespace to create visual hierarchy
10. Test with real data (not lorem ipsum)

---

## 3. Design System

### 3.1 Component Hierarchy

```
┌─ Pages (Full screens)
│  ├─ Layouts (Page structure)
│  │  ├─ Sections (Major divisions)
│  │  │  ├─ Components (Reusable blocks)
│  │  │  │  ├─ Elements (Atomic units)
│  │  │  │  │  └─ Primitives (HTML elements)
```

### 3.2 Atomic Design Elements

**Button:**
```css
/* Primary Button */
.btn-primary {
  background: #3B82F6;
  color: #FFFFFF;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #2563EB;
}

.btn-primary:disabled {
  background: #9CA3AF;
  cursor: not-allowed;
}

/* Secondary Button */
.btn-secondary {
  background: #FFFFFF;
  color: #374151;
  border: 1px solid #D1D5DB;
  /* same padding/radius */
}

/* Sizes */
.btn-sm { padding: 6px 12px; font-size: 14px; }
.btn-md { padding: 10px 20px; font-size: 16px; }
.btn-lg { padding: 14px 28px; font-size: 18px; }
```

**Input Field:**
```css
.input-field {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #D1D5DB;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.2s;
}

.input-field:focus {
  border-color: #3B82F6;
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input-field.error {
  border-color: #EF4444;
}

.input-field:disabled {
  background: #F3F4F6;
  cursor: not-allowed;
}
```

**Card:**
```css
.card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 12px;
}

.card-content {
  color: #374151;
  font-size: 16px;
  line-height: 1.5;
}
```

**Badge:**
```css
.badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
}

.badge-success { background: #D1FAE5; color: #065F46; }
.badge-warning { background: #FEF3C7; color: #92400E; }
.badge-error { background: #FEE2E2; color: #991B1B; }
.badge-info { background: #DBEAFE; color: #1E40AF; }
```

### 3.3 Layout Patterns

**Grid System:**
```css
/* 12-column grid */
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 32px;
}

.row {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 24px;
}

.col-3 { grid-column: span 3; }  /* 25% */
.col-4 { grid-column: span 4; }  /* 33% */
.col-6 { grid-column: span 6; }  /* 50% */
.col-8 { grid-column: span 8; }  /* 66% */
.col-12 { grid-column: span 12; } /* 100% */
```

**Standard Page Layout:**
```
┌─────────────────────────────────────────┐
│ Header (64px fixed)                      │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ Page Title + Actions (80px)         │ │
│ ├─────────────────────────────────────┤ │
│ │                                      │ │
│ │ Content Area (scrollable)            │ │
│ │                                      │ │
│ │ ┌───────┐ ┌───────┐ ┌───────┐      │ │
│ │ │ Card  │ │ Card  │ │ Card  │      │ │
│ │ └───────┘ └───────┘ └───────┘      │ │
│ │                                      │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## 4. Page-by-Page Specifications

### 4.1 PAGE 1: Single Patent Analysis

**Route:** `/analyze/:patent_id`  
**Primary Use Case:** [[Use-Cases-Summary#UC-01]]  
**API Endpoint:** `POST /api/v1/analyze`

#### 4.1.1 Page Layout

```
┌────────────────────────────────────────────────────────┐
│ HEADER                                                  │
├────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────┐ │
│ │ SECTION A: Patent Header                           │ │
│ │ - Patent number (large, monospace)                 │ │
│ │ - Title (truncated at 100 chars)                   │ │
│ │ - Assignee, Filing date, Status                    │ │
│ └────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌────────────────────────────────────────────────────┐ │
│ │ SECTION B: Category Card (Hero)                    │ │
│ │ - Large category badge                             │ │
│ │ - One-sentence explanation                         │ │
│ │ - Recommendation (HOLD / MONETIZE / ABANDON)       │ │
│ └────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                  │
│ │4D Scores (4 cards, horizontal)                      │ │
│ │                                                      │ │
│ │ SECTION C: Dimension Scores                         │ │
│ └──────┴──────┴──────┴──────┘                         │
│                                                         │
│ ┌────────────────────────────────────────────────────┐ │
│ │ SECTION D: Score Details (Expandable)              │ │
│ │ - Breakdown by dimension                           │ │
│ │ - Formulas and calculations                        │ │
│ └────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌────────────────────────────────────────────────────┐ │
│ │ SECTION E: Licensing Intelligence (if applicable)  │ │
│ │ - Top 5 potential licensees                        │ │
│ │ - Fit scores with explanations                     │ │
│ └────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌────────────────────────────────────────────────────┐ │
│ │ SECTION F: Actions                                 │ │
│ │ [Export PDF] [Add to Portfolio] [Compare]          │ │
│ └────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

#### 4.1.2 SECTION A: Patent Header

**Purpose:** Establish context - what patent are we looking at?

**API Response Mapping:**
```json
{
  "patent_id": "EP1234567B1",
  "title": "Method and apparatus for...",
  "assignee": "Siemens AG",
  "filing_date": "2015-03-15",
  "grant_date": "2018-06-20",
  "status": "granted"
}
```

**Visual Design:**

```
┌─────────────────────────────────────────────────────┐
│ EP1234567B1                                   ⚙ ✕   │ ← Patent # + Actions
│ Method and apparatus for signal processing in...    │ ← Title (truncate)
│ Siemens AG · Filed Mar 15, 2015 · Granted          │ ← Metadata
└─────────────────────────────────────────────────────┘
```

**Component Structure:**

```tsx
<PatentHeader>
  <PatentNumber>EP1234567B1</PatentNumber>
  <PatentTitle tooltip={fullTitle}>
    {truncate(title, 100)}
  </PatentTitle>
  <PatentMetadata>
    <MetaItem icon="🏢">{assignee}</MetaItem>
    <MetaItem icon="📅">Filed {formatDate(filing_date)}</MetaItem>
    <MetaItem><Badge variant="success">Granted</Badge></MetaItem>
  </PatentMetadata>
</PatentHeader>
```

**Typography:**
- Patent Number: `JetBrains Mono, 24px, #111827`
- Title: `Inter, 18px, #374151`
- Metadata: `Inter, 14px, #6B7280`

**Interactions:**
- Hover patent number → Show copy button
- Click title → Expand to full title
- Click assignee → Filter by assignee
- Click ⚙ → Show advanced options
- Click ✕ → Close analysis

**Edge Cases:**
- Very long title (>100 chars) → Truncate with "..."
- No grant date → Show "Pending"
- Multiple assignees → Show first + "and X others"

**Risk:** Title truncation loses context  
**Mitigation:** Tooltip on hover shows full title

#### 4.1.3 SECTION B: Category Card (Hero Section)

**Purpose:** Answer the #1 question: "What should I do with this patent?"

**API Response Mapping:**
```json
{
  "synthesis": {
    "category": "HIDDEN_GEM",
    "rationale": "Low citation count but excellent legal strength...",
    "recommendation": "MONETIZE",
    "priority": "HIGH"
  }
}
```

**Visual Design:**

```
┌───────────────────────────────────────────────────────┐
│  💎 HIDDEN GEM                                   HIGH │ ← Category + Priority
│                                                        │
│  This patent has low citation impact but strong legal │ ← Rationale
│  position and high financial efficiency. Excellent    │
│  candidate for licensing or strategic partnerships.   │
│                                                        │
│  Recommendation: MONETIZE                             │ ← Action
│  ┌──────────────┐  ┌──────────────┐                  │
│  │ Find Targets │  │ Export Report│                  │ ← CTAs
│  └──────────────┘  └──────────────┘                  │
└───────────────────────────────────────────────────────┘
```

**Category Visual System:**

```
CROWN_JEWEL     → 👑 Purple background, gold accent
HIDDEN_GEM      → 💎 Blue-green background, emerald accent
RISING_STAR     → ⭐ Yellow background, gold accent
STRATEGIC_HOLD  → 🛡️ Blue background, navy accent
COST_DRAIN      → 💸 Red background, dark red accent
AGING_ASSET     → ⏳ Gray background, dark gray accent
```

**Component Structure:**

```tsx
<CategoryCard category={category}>
  <CategoryHeader>
    <CategoryIcon>{getIcon(category)}</CategoryIcon>
    <CategoryName>{category.replace('_', ' ')}</CategoryName>
    <PriorityBadge level={priority}>{priority}</PriorityBadge>
  </CategoryHeader>
  
  <CategoryRationale>
    {synthesis.rationale}
  </CategoryRationale>
  
  <CategoryRecommendation>
    <strong>Recommendation:</strong> {recommendation}
  </CategoryRecommendation>
  
  <CategoryActions>
    {recommendation === 'MONETIZE' && (
      <Button primary onClick={findLicensees}>Find Targets</Button>
    )}
    <Button secondary onClick={exportReport}>Export Report</Button>
  </CategoryActions>
</CategoryCard>
```

**Typography:**
- Category Name: `Inter, 28px, Bold, Category Color`
- Rationale: `Inter, 16px, #374151, line-height 1.6`
- Recommendation: `Inter, 18px, Semi-bold, #111827`

**Interactions:**
- Click category name → Show category explanation modal
- Click "Find Targets" → Scroll to licensing section
- Click "Export Report" → Generate PDF

**Edge Cases:**
- Multiple recommendations → Show primary + "See details"
- Low confidence → Show warning badge

**Risk:** Category name not understood by user  
**Mitigation:** 
- Icon + color coding (visual)
- Rationale explains in plain English (textual)
- "?" icon next to category opens explanation

#### 4.1.4 SECTION C: 4D Dimension Scores

**Purpose:** Show detailed scoring across all 4 dimensions

**API Response Mapping:**
```json
{
  "dimensions": {
    "influence": {
      "score": 48,
      "confidence": "HIGH",
      "trend": "stable"
    },
    "legal": {
      "score": 98,
      "confidence": "HIGH",
      "trend": "strengthening"
    },
    "financial": {
      "score": 91,
      "confidence": "HIGH",
      "trend": "improving"
    },
    "future": {
      "score": 76,
      "confidence": "HIGH",
      "predicted_citations_3yr": 18
    }
  }
}
```

**Visual Design:**

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ INFLUENCE    │ │ LEGAL        │ │ FINANCIAL    │ │ FUTURE       │
│              │ │              │ │              │ │              │
│      48      │ │      98      │ │      91      │ │      76      │
│   ════════   │ │   ════════   │ │   ════════   │ │   ════════   │
│              │ │              │ │              │ │              │
│ Citations:25 │ │ Granted ✓   │ │ Cost/Cite:   │ │ Predicted:   │
│ Velocity:2.5 │ │ Opposition ✓│ │ €1,151       │ │ 18 cites     │
│              │ │              │ │              │ │              │
│ [Details] →  │ │ [Details] →  │ │ [Details] →  │ │ [Details] →  │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

**Component Structure:**

```tsx
<DimensionScores>
  {dimensions.map(dimension => (
    <DimensionCard key={dimension.name} color={dimension.color}>
      <DimensionHeader>
        <DimensionIcon>{dimension.icon}</DimensionIcon>
        <DimensionName>{dimension.name}</DimensionName>
      </DimensionHeader>
      
      <ScoreDisplay>
        <ScoreNumber>{dimension.score}</ScoreNumber>
        <ScoreBar value={dimension.score} max={100} />
        <ConfidenceBadge>{dimension.confidence}</ConfidenceBadge>
      </ScoreDisplay>
      
      <KeyMetrics>
        {dimension.top_metrics.map(metric => (
          <Metric key={metric.name}>
            <MetricLabel>{metric.label}:</MetricLabel>
            <MetricValue>{metric.value}</MetricValue>
          </Metric>
        ))}
      </KeyMetrics>
      
      <ExpandButton onClick={() => expandDimension(dimension.name)}>
        Details →
      </ExpandButton>
    </DimensionCard>
  ))}
</DimensionScores>
```

**Score Visualization:**

```tsx
// Score Number with color coding
function ScoreNumber({ value }) {
  const color = 
    value >= 75 ? '#10B981' :  // Green (good)
    value >= 50 ? '#F59E0B' :  // Amber (medium)
                  '#EF4444';   // Red (poor)
  
  return (
    <div style={{ 
      fontSize: '48px',
      fontWeight: '700',
      color: color
    }}>
      {value}
    </div>
  );
}

// Score Bar (horizontal progress)
function ScoreBar({ value, max }) {
  const percentage = (value / max) * 100;
  
  return (
    <div style={{ 
      width: '100%',
      height: '8px',
      background: '#E5E7EB',
      borderRadius: '4px',
      overflow: 'hidden'
    }}>
      <div style={{
        width: `${percentage}%`,
        height: '100%',
        background: getScoreColor(value),
        transition: 'width 0.5s ease'
      }} />
    </div>
  );
}
```

**Interactions:**
- Hover card → Slight elevation (shadow increase)
- Click "Details" → Expand inline to show breakdown
- Click score number → Show explanation modal

**Edge Cases:**
- Low confidence → Show "?" icon + warning
- Missing dimension → Show "N/A" with explanation
- Score exactly 0 or 100 → Validate with backend

**Risk:** User doesn't understand what scores mean  
**Mitigation:**
- Color coding (green=good, red=bad)
- Show 2-3 key metrics below score
- "Details" button reveals calculation
- Comparison to benchmark ("Above average")

#### 4.1.5 SECTION D: Score Details (Expandable)

**Purpose:** Show calculation breakdown for transparency

**API Response Mapping:**
```json
{
  "dimensions": {
    "influence": {
      "score": 48,
      "metrics": {
        "velocity": 25.0,
        "field_normalized": 83.3,
        "h_index": 40.0,
        "diversity": 83.3
      },
      "formula": "weighted_sum",
      "weights": {
        "velocity": 0.20,
        "field_normalized": 0.50,
        "h_index": 0.20,
        "diversity": 0.10
      }
    }
  }
}
```

**Visual Design (Expanded):**

```
┌────────────────────────────────────────────────────────┐
│ INFLUENCE SCORE: 48                                 ▼  │ ← Click to collapse
├────────────────────────────────────────────────────────┤
│ Calculation Breakdown                                   │
│                                                         │
│ Component Scores:                                       │
│ • Citation Velocity:        25.0  (Weight: 20%)        │
│ • Field-Normalized Impact:  83.3  (Weight: 50%) ⭐     │
│ • H-Index:                  40.0  (Weight: 20%)        │
│ • Backward Diversity:       83.3  (Weight: 10%)        │
│                                                         │
│ Final Score: (25.0 × 0.20) + (83.3 × 0.50) +          │
│              (40.0 × 0.20) + (83.3 × 0.10) = 48.0      │
│                                                         │
│ Interpretation:                                         │
│ Despite low citation velocity, field-normalized impact │
│ is strong (83.3), indicating quality citations from    │
│ influential patents.                                    │
│                                                         │
│ [Show Raw Data] [Export Calculation]                   │
└────────────────────────────────────────────────────────┘
```

**Component Structure:**

```tsx
<ScoreDetails expanded={isExpanded}>
  <DetailsHeader onClick={() => setExpanded(!isExpanded)}>
    <DimensionName>INFLUENCE SCORE: {score}</DimensionName>
    <ExpandIcon>{isExpanded ? '▼' : '▶'}</ExpandIcon>
  </DetailsHeader>
  
  {isExpanded && (
    <DetailsContent>
      <ComponentScores>
        {Object.entries(metrics).map(([name, value]) => (
          <ComponentScore key={name}>
            <ComponentName>{formatName(name)}</ComponentName>
            <ComponentValue>{value.toFixed(1)}</ComponentValue>
            <ComponentWeight>(Weight: {weights[name] * 100}%)</ComponentWeight>
            {value > 75 && <HighlightStar>⭐</HighlightStar>}
          </ComponentScore>
        ))}
      </ComponentScores>
      
      <FormulaDisplay>
        <FormulaTitle>Final Score:</FormulaTitle>
        <Formula>{generateFormula(metrics, weights)}</Formula>
      </FormulaDisplay>
      
      <Interpretation>
        <InterpretationTitle>Interpretation:</InterpretationTitle>
        <InterpretationText>{generateInterpretation(metrics)}</InterpretationText>
      </Interpretation>
      
      <DetailsActions>
        <Button secondary onClick={showRawData}>Show Raw Data</Button>
        <Button secondary onClick={exportCalculation}>Export Calculation</Button>
      </DetailsActions>
    </DetailsContent>
  )}
</ScoreDetails>
```

**Formula Generation Logic:**

```tsx
function generateFormula(metrics, weights) {
  const terms = Object.entries(metrics).map(([name, value], index) => {
    const weight = weights[name];
    const isLast = index === Object.keys(metrics).length - 1;
    
    return `(${value.toFixed(1)} × ${weight.toFixed(2)})${isLast ? '' : ' + '}`;
  });
  
  const result = Object.entries(metrics).reduce((sum, [name, value]) => {
    return sum + (value * weights[name]);
  }, 0);
  
  return `${terms.join('\n')} = ${result.toFixed(1)}`;
}
```

**Interactions:**
- Click header → Toggle expand/collapse
- Click component name → Show definition tooltip
- Click "Show Raw Data" → Modal with JSON response
- Click "Export Calculation" → Download CSV with breakdown

**Edge Cases:**
- All components equal → Note this is unusual
- One component dominates (>80%) → Highlight with warning
- Negative values → Should not happen, show error

**Risk:** Formula overwhelms non-technical users  
**Mitigation:**
- Hide behind "Details" expansion (progressive disclosure)
- Provide interpretation in plain English
- Use visual weights (bar charts) not just numbers

#### 4.1.6 SECTION E: Licensing Intelligence

**Purpose:** Actionable recommendations for monetization

**API Response Mapping:**
```json
{
  "licensing_targets": [
    {
      "company_name": "Acme Technology Inc.",
      "fit_score": 81,
      "fit_breakdown": {
        "technology": 85,
        "geography": 80,
        "size": 75,
        "ip_sophistication": 90,
        "growth": 75
      },
      "reasoning": "Strong technology fit in G06F space...",
      "estimated_value_min": 150000,
      "estimated_value_max": 400000
    }
    // ... 4 more
  ]
}
```

**Visual Design:**

```
┌─────────────────────────────────────────────────────────┐
│ LICENSING OPPORTUNITIES                                  │
│                                                          │
│ Top 5 Potential Licensees                               │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 1. Acme Technology Inc.                    FIT: 81 │  │
│ │    ████████████████████████████████░░░░░░░ 81/100  │  │
│ │                                                     │  │
│ │    Strong technology fit in G06F semiconductor      │  │
│ │    manufacturing. Active in EU markets. Growing     │  │
│ │    IP portfolio (+15% YoY).                         │  │
│ │                                                     │  │
│ │    Est. Value: €150K - €400K                        │  │
│ │                                                     │  │
│ │    [View Details] [Export Contact Sheet]            │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 2. TechCorp GmbH                           FIT: 78 │  │
│ │    ... [similar structure] ...                      │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ [Show All 47 Candidates] [Customize Filters]            │
└─────────────────────────────────────────────────────────┘
```

**Component Structure:**

```tsx
<LicensingSection>
  <SectionHeader>
    <SectionTitle>LICENSING OPPORTUNITIES</SectionTitle>
    <SectionSubtitle>Top 5 Potential Licensees</SectionSubtitle>
  </SectionHeader>
  
  <TargetList>
    {licensing_targets.slice(0, 5).map((target, index) => (
      <TargetCard key={target.company_name} rank={index + 1}>
        <TargetHeader>
          <TargetRank>{index + 1}.</TargetRank>
          <TargetName>{target.company_name}</TargetName>
          <FitScore value={target.fit_score}>
            FIT: {target.fit_score}
          </FitScore>
        </TargetHeader>
        
        <FitBar value={target.fit_score} max={100} />
        
        <TargetReasoning>{target.reasoning}</TargetReasoning>
        
        <EstimatedValue>
          <ValueLabel>Est. Value:</ValueLabel>
          <ValueRange>
            {formatCurrency(target.estimated_value_min)} - {formatCurrency(target.estimated_value_max)}
          </ValueRange>
        </EstimatedValue>
        
        <TargetActions>
          <Button secondary onClick={() => viewDetails(target)}>
            View Details
          </Button>
          <Button secondary onClick={() => exportContact(target)}>
            Export Contact Sheet
          </Button>
        </TargetActions>
      </TargetCard>
    ))}
  </TargetList>
  
  <SectionActions>
    <Button primary onClick={showAllCandidates}>
      Show All {licensing_targets.length} Candidates
    </Button>
    <Button secondary onClick={customizeFilters}>
      Customize Filters
    </Button>
  </SectionActions>
</LicensingSection>
```

**Fit Score Visualization:**

```tsx
function FitBar({ value, max }) {
  // Color gradient based on fit score
  const color = 
    value >= 80 ? '#10B981' :  // Green
    value >= 60 ? '#F59E0B' :  // Amber
                  '#6B7280';   // Gray
  
  return (
    <div className="fit-bar-container">
      <div 
        className="fit-bar-fill"
        style={{
          width: `${(value / max) * 100}%`,
          background: color
        }}
      />
      <div className="fit-bar-label">
        {value}/100
      </div>
    </div>
  );
}
```

**Interactions:**
- Click company name → Open company modal with full profile
- Click "View Details" → Show fit breakdown (5 categories)
- Click "Export Contact Sheet" → Download PDF with company info
- Click "Show All Candidates" → Navigate to full list page
- Click "Customize Filters" → Open filter modal

**Fit Breakdown Modal:**

```
┌─────────────────────────────────────────────────┐
│ Acme Technology Inc. - Fit Analysis         ✕   │
├─────────────────────────────────────────────────┤
│                                                  │
│ Overall Fit: 81/100                              │
│                                                  │
│ Technology Match:         85  ██████████████▓░  │
│ Geographic Overlap:       80  ████████████▓░░░  │
│ Company Size Match:       75  ████████████░░░░  │
│ IP Sophistication:        90  ██████████████▓░  │
│ Growth Trajectory:        75  ████████████░░░░  │
│                                                  │
│ Why This Company?                                │
│ • Active in G06F (semiconductor manufacturing)   │
│ • 47 patents in related space (IPC overlap)      │
│ • EU presence (DE, FR, UK facilities)            │
│ • Growing IP portfolio (+15% YoY)                │
│ • Revenue €250M (mid-size, acquisition budget)   │
│                                                  │
│ Estimated Licensing Value: €150K - €400K         │
│ Confidence: MEDIUM (based on comparable deals)   │
│                                                  │
│ [Download Full Report] [Add to CRM]              │
└─────────────────────────────────────────────────┘
```

**Edge Cases:**
- No licensing targets → Show "Not applicable for this category"
- Very wide value range → Explain uncertainty
- Unknown company → Show company research button

**Risk:** Estimated values are inaccurate  
**Mitigation:**
- Show wide range (min-max)
- Label as "estimate" not "price"
- Show confidence level
- Explain methodology in tooltip

**Risk:** User acts on recommendation without validation  
**Mitigation:**
- Prominent disclaimer: "For informational purposes only"
- Suggest "Validate with patent attorney"
- Link to methodology documentation

#### 4.1.7 SECTION F: Page Actions

**Purpose:** Enable next steps

**Visual Design:**

```
┌──────────────────────────────────────────────────────┐
│ [⬇ Export PDF Report] [📁 Add to Portfolio]         │
│ [📊 Compare with Similar] [🔗 Share Link]            │
└──────────────────────────────────────────────────────┘
```

**Component Structure:**

```tsx
<PageActions>
  <PrimaryActions>
    <Button primary icon="⬇" onClick={exportPDF}>
      Export PDF Report
    </Button>
    <Button primary icon="📁" onClick={addToPortfolio}>
      Add to Portfolio
    </Button>
  </PrimaryActions>
  
  <SecondaryActions>
    <Button secondary icon="📊" onClick={comparePatents}>
      Compare with Similar
    </Button>
    <Button secondary icon="🔗" onClick={shareLink}>
      Share Link
    </Button>
  </SecondaryActions>
</PageActions>
```

**Action Behaviors:**

**Export PDF:**
1. Click button → Show loading spinner
2. Generate PDF server-side (include all sections)
3. Download starts automatically
4. Toast: "Report downloaded successfully"

**Add to Portfolio:**
1. Click button → Show portfolio selector modal
2. User selects portfolio or creates new
3. Add patent to portfolio
4. Toast: "Added to [Portfolio Name]"
5. Button changes to "✓ In Portfolio"

**Compare with Similar:**
1. Click button → Show comparison modal
2. User searches for patents to compare
3. Navigate to comparison view (new page)

**Share Link:**
1. Click button → Copy URL to clipboard
2. Toast: "Link copied! Valid for 24 hours"
3. Generate shareable token (expires 24h)

**Edge Cases:**
- PDF generation fails → Show error + retry button
- Patent already in portfolio → Show "Already added"
- No similar patents → Disable compare button

**Risk:** PDF generation is slow (>5s)  
**Mitigation:**
- Show progress bar with percentage
- Allow user to continue using app (background generation)
- Email PDF when complete (for >10s generation)

---

### 4.2 PAGE 2: Portfolio Analysis

**Route:** `/portfolio/:company_name`  
**Primary Use Case:** [[Use-Cases-Summary#UC-02]]  
**API Endpoint:** `POST /api/v1/portfolio`

#### 4.2.1 Page Layout

```
┌──────────────────────────────────────────────────────┐
│ HEADER                                                │
├──────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────┐ │
│ │ SECTION A: Company Header                        │ │
│ │ - Company name + logo                            │ │
│ │ - Patent count + date range                      │ │
│ └──────────────────────────────────────────────────┘ │
│                                                       │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                │
│ │ KPIs (4 cards, horizontal)                        │ │
│ │ SECTION B: Key Metrics                            │ │
│ └──────┴──────┴──────┴──────┘                       │
│                                                       │
│ ┌─────────────────┐ ┌─────────────────┐             │
│ │ SECTION C:      │ │ SECTION D:      │             │
│ │ Portfolio Health│ │ Category Dist.  │             │
│ │ (Score + Chart) │ │ (Pie Chart)     │             │
│ └─────────────────┘ └─────────────────┘             │
│                                                       │
│ ┌────────────────────────────────────────────────┐  │
│ │ SECTION E: Financial Overview                  │  │
│ │ - Total costs, annual maintenance, efficiency  │  │
│ └────────────────────────────────────────────────┘  │
│                                                       │
│ ┌────────────────────────────────────────────────┐  │
│ │ SECTION F: Optimization Recommendations        │  │
│ │ - Cost savings opportunities                   │  │
│ │ - Licensing opportunities                      │  │
│ │ - Abandonment candidates                       │  │
│ └────────────────────────────────────────────────┘  │
│                                                       │
│ ┌────────────────────────────────────────────────┐  │
│ │ SECTION G: Patent List (Table)                 │  │
│ │ - Sortable, filterable                         │  │
│ │ - Action buttons per patent                    │  │
│ └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

#### 4.2.2 SECTION A: Company Header

**API Response:**
```json
{
  "company": {
    "name": "Siemens AG",
    "han_id": 12345,
    "total_patents": 2847,
    "analyzed_patents": 500
  },
  "filters_applied": {
    "filing_year_min": 2015,
    "filing_year_max": 2024,
    "status": "granted"
  }
}
```

**Visual Design:**

```
┌───────────────────────────────────────────────────────┐
│ [Logo] Siemens AG                            [Edit] ✕ │
│ 500 patents analyzed · 2015-2024 · Granted only       │
│ Last updated: Dec 15, 2024                             │
└───────────────────────────────────────────────────────┘
```

**Component Structure:**

```tsx
<CompanyHeader>
  <CompanyIdentity>
    <CompanyLogo src={company.logo_url} alt={company.name} />
    <CompanyName>{company.name}</CompanyName>
  </CompanyIdentity>
  
  <AnalysisMetadata>
    <MetaItem>
      <strong>{company.analyzed_patents}</strong> patents analyzed
    </MetaItem>
    <MetaSeparator>·</MetaSeparator>
    <MetaItem>
      {filters.filing_year_min}-{filters.filing_year_max}
    </MetaItem>
    <MetaSeparator>·</MetaSeparator>
    <MetaItem>
      {filters.status} only
    </MetaItem>
  </AnalysisMetadata>
  
  <UpdateInfo>
    Last updated: {formatDateTime(analysis.timestamp)}
  </UpdateInfo>
  
  <HeaderActions>
    <Button secondary onClick={editFilters}>Edit</Button>
    <IconButton onClick={closeAnalysis}>✕</IconButton>
  </HeaderActions>
</CompanyHeader>
```

**Interactions:**
- Click "Edit" → Reopen filter modal
- Click ✕ → Return to search
- Click company name → Show company info modal

**Edge Cases:**
- No logo → Show company initials
- Sampled portfolio → Show "(Sampled from 2847 total)"

#### 4.2.3 SECTION B: Key Performance Indicators

**API Response:**
```json
{
  "summary": {
    "total_patents": 500,
    "avg_influence": 52.3,
    "avg_legal": 76.8,
    "avg_financial": 68.4,
    "avg_future": 61.2
  }
}
```

**Visual Design:**

```
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  INFLUENCE  │ │    LEGAL    │ │  FINANCIAL  │ │   FUTURE    │
│             │ │             │ │             │ │             │
│     52      │ │     77      │ │     68      │ │     61      │
│  ▲ +3.2%    │ │  ► Stable   │ │  ▼ -1.8%    │ │  ▲ +5.1%    │
│             │ │             │ │             │ │             │
│  Medium     │ │    Good     │ │    Good     │ │   Medium    │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

**Component Structure:**

```tsx
<KPICards>
  {dimensions.map(dimension => (
    <KPICard key={dimension.name} color={dimension.color}>
      <KPIDimensionName>{dimension.name}</KPIDimensionName>
      
      <KPIScore value={dimension.avg_score}>
        {dimension.avg_score.toFixed(0)}
      </KPIScore>
      
      <KPITrend change={dimension.change_vs_benchmark}>
        <TrendIcon>{getTrendIcon(dimension.change)}</TrendIcon>
        <TrendValue>
          {dimension.change > 0 ? '+' : ''}
          {dimension.change.toFixed(1)}%
        </TrendValue>
      </KPITrend>
      
      <KPILabel level={getLevel(dimension.avg_score)}>
        {getLevel(dimension.avg_score)}
      </KPILabel>
    </KPICard>
  ))}
</KPICards>
```

**Trend Calculation:**

```tsx
// Trend vs. industry benchmark or prior analysis
function getTrendIcon(change) {
  if (change > 2) return '▲';  // Significant increase
  if (change < -2) return '▼'; // Significant decrease
  return '►';                   // Stable
}

function getLevel(score) {
  if (score >= 75) return 'Excellent';
  if (score >= 60) return 'Good';
  if (score >= 45) return 'Medium';
  return 'Needs Attention';
}
```

**Interactions:**
- Click card → Filter portfolio by this dimension
- Hover → Show detailed statistics

**Edge Cases:**
- First analysis → No trend data → Hide trend
- All scores similar → Note portfolio homogeneity

#### 4.2.4 SECTION C: Portfolio Health Score

**API Response:**
```json
{
  "portfolio_health": {
    "overall_score": 68,
    "breakdown": {
      "quality": 72,
      "efficiency": 65,
      "future_potential": 68,
      "strategic_fit": 67
    },
    "grade": "B"
  }
}
```

**Visual Design:**

```
┌──────────────────────────────────────┐
│ PORTFOLIO HEALTH                      │
│                                       │
│         68                            │
│      ═════════                        │
│         B                             │
│                                       │
│ Good overall health with              │
│ opportunities for optimization        │
│                                       │
│ Breakdown:                            │
│ Quality           ██████████ 72      │
│ Efficiency        ████████░░ 65      │
│ Future Potential  █████████░ 68      │
│ Strategic Fit     █████████░ 67      │
│                                       │
│ [View Recommendations]                │
└──────────────────────────────────────┘
```

**Component Structure:**

```tsx
<PortfolioHealthCard>
  <CardTitle>PORTFOLIO HEALTH</CardTitle>
  
  <HealthScore>
    <ScoreCircle value={health.overall_score}>
      <ScoreNumber>{health.overall_score}</ScoreNumber>
      <ScoreGrade>{health.grade}</ScoreGrade>
    </ScoreCircle>
  </HealthScore>
  
  <HealthSummary>{health.summary_text}</HealthSummary>
  
  <HealthBreakdown>
    <BreakdownTitle>Breakdown:</BreakdownTitle>
    {Object.entries(health.breakdown).map(([category, score]) => (
      <BreakdownItem key={category}>
        <ItemLabel>{formatLabel(category)}</ItemLabel>
        <ItemBar value={score} max={100} />
        <ItemScore>{score}</ItemScore>
      </BreakdownItem>
    ))}
  </HealthBreakdown>
  
  <CardActions>
    <Button primary onClick={viewRecommendations}>
      View Recommendations
    </Button>
  </CardActions>
</PortfolioHealthCard>
```

**Score Circle Visualization:**

```tsx
function ScoreCircle({ value, children }) {
  const circumference = 2 * Math.PI * 45; // radius = 45
  const progress = (value / 100) * circumference;
  
  return (
    <svg width="120" height="120">
      {/* Background circle */}
      <circle
        cx="60"
        cy="60"
        r="45"
        fill="none"
        stroke="#E5E7EB"
        strokeWidth="8"
      />
      {/* Progress circle */}
      <circle
        cx="60"
        cy="60"
        r="45"
        fill="none"
        stroke={getScoreColor(value)}
        strokeWidth="8"
        strokeDasharray={circumference}
        strokeDashoffset={circumference - progress}
        transform="rotate(-90 60 60)"
      />
      {/* Center content */}
      <foreignObject x="0" y="0" width="120" height="120">
        <div className="score-circle-content">
          {children}
        </div>
      </foreignObject>
    </svg>
  );
}
```

**Grading System:**

```
A+  95-100  Exceptional
A   90-94   Excellent
B+  85-89   Very Good
B   75-84   Good
C+  65-74   Above Average
C   55-64   Average
D   45-54   Below Average
F   0-44    Needs Attention
```

**Interactions:**
- Click "View Recommendations" → Jump to optimization section
- Hover breakdown item → Show detailed explanation

**Edge Cases:**
- Very low health (<40) → Show urgent warning
- Very high health (>90) → Show congratulations
- First portfolio → No comparison data

**Risk:** User doesn't know how to improve score  
**Mitigation:**
- "View Recommendations" button provides actionable items
- Each breakdown component has improvement tips

#### 4.2.5 SECTION D: Category Distribution

**API Response:**
```json
{
  "distribution": {
    "by_category": {
      "CROWN_JEWEL": 42,
      "HIDDEN_GEM": 67,
      "RISING_STAR": 53,
      "STRATEGIC_HOLD": 198,
      "COST_DRAIN": 89,
      "AGING_ASSET": 51
    }
  }
}
```

**Visual Design:**

```
┌───────────────────────────────────────┐
│ CATEGORY DISTRIBUTION                  │
│                                        │
│        [Donut Chart]                   │
│                                        │
│    198 Strategic Hold (39.6%)         │
│     89 Cost Drain (17.8%)              │
│     67 Hidden Gem (13.4%)              │
│     53 Rising Star (10.6%)             │
│     51 Aging Asset (10.2%)             │
│     42 Crown Jewel (8.4%)              │
│                                        │
│ Key Insight:                           │
│ Large strategic hold portfolio         │
│ indicates defensive positioning        │
│                                        │
│ [Filter by Category]                   │
└───────────────────────────────────────┘
```

**Component Structure:**

```tsx
<CategoryDistributionCard>
  <CardTitle>CATEGORY DISTRIBUTION</CardTitle>
  
  <DonutChart
    data={Object.entries(distribution.by_category).map(([name, count]) => ({
      label: formatCategoryName(name),
      value: count,
      color: getCategoryColor(name)
    }))}
    centerLabel={`${total} patents`}
  />
  
  <CategoryLegend>
    {sortedCategories.map(([name, count]) => (
      <LegendItem key={name} color={getCategoryColor(name)}>
        <LegendColor />
        <LegendLabel>{count} {formatCategoryName(name)}</LegendLabel>
        <LegendPercentage>({(count / total * 100).toFixed(1)}%)</LegendPercentage>
      </LegendItem>
    ))}
  </CategoryLegend>
  
  <KeyInsight>
    <InsightTitle>Key Insight:</InsightTitle>
    <InsightText>{generateInsight(distribution)}</InsightText>
  </KeyInsight>
  
  <CardActions>
    <Button secondary onClick={filterByCategory}>
      Filter by Category
    </Button>
  </CardActions>
</CategoryDistributionCard>
```

**Donut Chart Implementation:**

```tsx
function DonutChart({ data, centerLabel }) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  let cumulativePercentage = 0;
  
  return (
    <svg viewBox="0 0 200 200" className="donut-chart">
      {data.map((item, index) => {
        const percentage = (item.value / total) * 100;
        const startAngle = (cumulativePercentage / 100) * 360;
        const endAngle = ((cumulativePercentage + percentage) / 100) * 360;
        
        cumulativePercentage += percentage;
        
        return (
          <DonutSegment
            key={index}
            startAngle={startAngle}
            endAngle={endAngle}
            color={item.color}
            innerRadius={60}
            outerRadius={90}
          />
        );
      })}
      
      <text x="100" y="100" textAnchor="middle" className="center-label">
        {centerLabel}
      </text>
    </svg>
  );
}
```

**Insight Generation:**

```tsx
function generateInsight(distribution) {
  const sorted = Object.entries(distribution.by_category)
    .sort((a, b) => b[1] - a[1]);
  
  const topCategory = sorted[0][0];
  const topCount = sorted[0][1];
  const topPct = (topCount / Object.values(distribution.by_category).reduce((a, b) => a + b, 0)) * 100;
  
  const insights = {
    'STRATEGIC_HOLD': `Large strategic hold portfolio (${topPct.toFixed(0)}%) indicates defensive positioning`,
    'COST_DRAIN': `High cost drain percentage (${topPct.toFixed(0)}%) suggests need for optimization`,
    'HIDDEN_GEM': `Many hidden gems (${topPct.toFixed(0)}%) present licensing opportunities`,
    'CROWN_JEWEL': `Strong crown jewel concentration (${topPct.toFixed(0)}%) shows competitive moat`
  };
  
  return insights[topCategory] || 'Balanced portfolio distribution';
}
```

**Interactions:**
- Click segment → Filter patents by that category
- Hover segment → Show tooltip with count and percentage
- Click legend item → Same as clicking segment

**Edge Cases:**
- Single category dominates (>70%) → Warning message
- Very even distribution → Note this is unusual
- Zero in category → Don't show in legend

#### 4.2.6 SECTION E: Financial Overview

**API Response:**
```json
{
  "financial": {
    "total_cost_to_date": 14235000,
    "annual_maintenance": 1872000,
    "avg_cost_per_patent": 28470,
    "portfolio_efficiency": "GOOD",
    "cost_per_citation": 1847,
    "benchmark_cost_per_citation": 2100
  }
}
```

**Visual Design:**

```
┌──────────────────────────────────────────────────────┐
│ FINANCIAL OVERVIEW                                    │
├──────────────────────────────────────────────────────┤
│ Total Investment to Date          €14,235,000         │
│ Annual Maintenance Costs          €1,872,000          │
│ Average Cost per Patent           €28,470             │
│                                                        │
│ Portfolio Efficiency: GOOD                            │
│ ██████████████████░░ 88/100                           │
│                                                        │
│ Cost per Citation: €1,847                             │
│ (12% below industry average of €2,100)                │
│                                                        │
│ ┌────────────────────────────────────────────────┐   │
│ │ Cost Breakdown (Stacked Bar)                   │   │
│ │ ███████████ Filing/Prosecution (48%)           │   │
│ │ ██████ EPO Renewals (27%)                      │   │
│ │ ████ National Renewals (18%)                   │   │
│ │ ██ Validation (7%)                             │   │
│ └────────────────────────────────────────────────┘   │
│                                                        │
│ [View Cost Details] [Optimization Report]             │
└──────────────────────────────────────────────────────┘
```

**Component Structure:**

```tsx
<FinancialOverviewCard>
  <CardTitle>FINANCIAL OVERVIEW</CardTitle>
  
  <FinancialMetrics>
    <MetricRow>
      <MetricLabel>Total Investment to Date</MetricLabel>
      <MetricValue highlight>{formatCurrency(financial.total_cost_to_date)}</MetricValue>
    </MetricRow>
    <MetricRow>
      <MetricLabel>Annual Maintenance Costs</MetricLabel>
      <MetricValue>{formatCurrency(financial.annual_maintenance)}</MetricValue>
    </MetricRow>
    <MetricRow>
      <MetricLabel>Average Cost per Patent</MetricLabel>
      <MetricValue>{formatCurrency(financial.avg_cost_per_patent)}</MetricValue>
    </MetricRow>
  </FinancialMetrics>
  
  <EfficiencyScore>
    <EfficiencyLabel>Portfolio Efficiency: {financial.portfolio_efficiency}</EfficiencyLabel>
    <EfficiencyBar value={financial.efficiency_score} max={100} />
  </EfficiencyScore>
  
  <BenchmarkComparison>
    <ComparisonMetric>Cost per Citation: {formatCurrency(financial.cost_per_citation)}</ComparisonMetric>
    <ComparisonNote>
      ({financial.vs_benchmark}% {financial.vs_benchmark < 0 ? 'below' : 'above'} industry average of {formatCurrency(financial.benchmark_cost_per_citation)})
    </ComparisonNote>
  </BenchmarkComparison>
  
  <CostBreakdown>
    <BreakdownTitle>Cost Breakdown</BreakdownTitle>
    <StackedBar data={financial.cost_breakdown} />
  </CostBreakdown>
  
  <CardActions>
    <Button secondary onClick={viewCostDetails}>View Cost Details</Button>
    <Button primary onClick={viewOptimization}>Optimization Report</Button>
  </CardActions>
</FinancialOverviewCard>
```

**Stacked Bar Chart:**

```tsx
function StackedBar({ data }) {
  const total = Object.values(data).reduce((sum, val) => sum + val, 0);
  let cumulativeWidth = 0;
  
  return (
    <div className="stacked-bar">
      {Object.entries(data).map(([category, amount]) => {
        const width = (amount / total) * 100;
        const segment = (
          <div
            key={category}
            className="bar-segment"
            style={{
              width: `${width}%`,
              backgroundColor: getCostCategoryColor(category),
              marginLeft: cumulativeWidth > 0 ? '0' : undefined
            }}
            title={`${category}: ${formatCurrency(amount)} (${width.toFixed(0)}%)`}
          >
            {width > 10 && ( // Only show label if segment large enough
              <span className="segment-label">
                {category} ({width.toFixed(0)}%)
              </span>
            )}
          </div>
        );
        
        cumulativeWidth += width;
        return segment;
      })}
    </div>
  );
}
```

**Interactions:**
- Click "View Cost Details" → Modal with detailed breakdown
- Click "Optimization Report" → Jump to optimization section
- Hover stacked bar segment → Tooltip with exact amounts

**Edge Cases:**
- Very high costs → Warning message
- Costs below average → Congratulations message
- Missing cost data → Show estimate with disclaimer

**Risk:** User panics at high total cost  
**Mitigation:**
- Show cost per patent (normalized)
- Compare to industry average (context)
- Highlight efficiency score (positive framing)

#### 4.2.7 SECTION F: Optimization Recommendations

**API Response:**
```json
{
  "optimization": {
    "total_potential_savings": 456000,
    "abandonment_candidates": {
      "count": 89,
      "annual_savings": 267000,
      "patents": [...]
    },
    "geographic_optimization": {
      "count": 127,
      "annual_savings": 189000,
      "recommendations": [...]
    },
    "licensing_opportunities": {
      "count": 67,
      "estimated_revenue": 3500000
    }
  }
}
```

**Visual Design:**

```
┌────────────────────────────────────────────────────────┐
│ OPTIMIZATION OPPORTUNITIES                              │
│                                                         │
│ Total Potential Impact: €456K annual savings +          │
│                         €3.5M licensing revenue         │
│                                                         │
│ ┌────────────────────────────────────────────────────┐ │
│ │ 💰 Cost Savings Opportunities                      │ │
│ │                                                     │ │
│ │ Abandonment Candidates         €267K/year          │ │
│ │ 89 patents with minimal value                      │ │
│ │ [View List] [Generate Report]                      │ │
│ │                                                     │ │
│ │ Geographic Optimization        €189K/year          │ │
│ │ Trim low-ROI countries from 127 patents            │ │
│ │ [View Recommendations]                             │ │
│ └────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌────────────────────────────────────────────────────┐ │
│ │ 💎 Revenue Opportunities                           │ │
│ │                                                     │ │
│ │ Hidden Gems Licensing          €2.8M - €7.1M      │ │
│ │ 67 undervalued patents with licensing potential    │ │
│ │ [View Opportunities] [Export Report]               │ │
│ └────────────────────────────────────────────────────┘ │
│                                                         │
│ [Download Complete Optimization Report]                 │
└────────────────────────────────────────────────────────┘
```

**Component Structure:**

```tsx
<OptimizationSection>
  <SectionHeader>
    <SectionTitle>OPTIMIZATION OPPORTUNITIES</SectionTitle>
    <TotalImpact>
      Total Potential Impact: 
      <ImpactSavings>{formatCurrency(optimization.total_potential_savings)} annual savings</ImpactSavings>
      +
      <ImpactRevenue>{formatCurrencyRange(optimization.licensing_opportunities.estimated_revenue)} licensing revenue</ImpactRevenue>
    </TotalImpact>
  </SectionHeader>
  
  <OpportunityCards>
    <OpportunityCard type="cost_savings">
      <CardIcon>💰</CardIcon>
      <CardTitle>Cost Savings Opportunities</CardTitle>
      
      <Opportunity>
        <OpportunityName>Abandonment Candidates</OpportunityName>
        <OpportunitySavings highlight>
          {formatCurrency(optimization.abandonment_candidates.annual_savings)}/year
        </OpportunitySavings>
        <OpportunityDescription>
          {optimization.abandonment_candidates.count} patents with minimal value
        </OpportunityDescription>
        <OpportunityActions>
          <Button secondary onClick={() => viewList('abandonment')}>View List</Button>
          <Button secondary onClick={() => generateReport('abandonment')}>Generate Report</Button>
        </OpportunityActions>
      </Opportunity>
      
      <Opportunity>
        <OpportunityName>Geographic Optimization</OpportunityName>
        <OpportunitySavings highlight>
          {formatCurrency(optimization.geographic_optimization.annual_savings)}/year
        </OpportunitySavings>
        <OpportunityDescription>
          Trim low-ROI countries from {optimization.geographic_optimization.count} patents
        </OpportunityDescription>
        <OpportunityActions>
          <Button secondary onClick={() => viewRecommendations('geographic')}>View Recommendations</Button>
        </OpportunityActions>
      </Opportunity>
    </OpportunityCard>
    
    <OpportunityCard type="revenue">
      <CardIcon>💎</CardIcon>
      <CardTitle>Revenue Opportunities</CardTitle>
      
      <Opportunity>
        <OpportunityName>Hidden Gems Licensing</OpportunityName>
        <OpportunityRevenue highlight>
          {formatCurrencyRange(optimization.licensing_opportunities.estimated_revenue)}
        </OpportunityRevenue>
        <OpportunityDescription>
          {optimization.licensing_opportunities.count} undervalued patents with licensing potential
        </OpportunityDescription>
        <OpportunityActions>
          <Button secondary onClick={() => viewOpportunities('licensing')}>View Opportunities</Button>
          <Button secondary onClick={() => exportReport('licensing')}>Export Report</Button>
        </OpportunityActions>
      </Opportunity>
    </OpportunityCard>
  </OpportunityCards>
  
  <SectionActions>
    <Button primary onClick={downloadCompleteReport}>
      Download Complete Optimization Report
    </Button>
  </SectionActions>
</OptimizationSection>
```

**Abandonment Candidates Modal:**

```
┌───────────────────────────────────────────────────────────┐
│ Abandonment Candidates (89 patents)                   ✕   │
├───────────────────────────────────────────────────────────┤
│                                                            │
│ [Search patents...] [Filter by: All ▼] [Sort by: Savings ▼] │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐│
│ │Patent          Cost/yr  Impact  Age  Last Cite  Action││
│ ├────────────────────────────────────────────────────────┤│
│ │EP8765432B1     €4,200   None    9yr  2018       [ ]   ││
│ │                                                        ││
│ │Zero forward citations in 5 years. No licensing        ││
│ │interest. No related products.                         ││
│ │                                                        ││
│ │Recommendation: Abandon                                ││
│ │Risk: LOW - No dependencies identified                 ││
│ │                                                        ││
│ │[Abandon] [Keep] [Review Later]                        ││
│ └────────────────────────────────────────────────────────┘│
│                                                            │
│ [Similar items for remaining 88 patents...]               │
│                                                            │
│ Total Selected: 0 · Potential Savings: €0/year            │
│                                                            │
│ [Bulk Actions ▼] [Export List] [Close]                    │
└───────────────────────────────────────────────────────────┘
```

**Interactions:**
- Click "View List" → Open abandonment candidates modal
- Select patents → Enable bulk actions
- Click "Abandon" → Mark for abandonment (reversible)
- Click "Generate Report" → PDF with detailed analysis

**Edge Cases:**
- No optimization opportunities → Show "Portfolio already optimized"
- Very aggressive recommendations → Show risk warnings
- Recent changes → Note "Analysis may be outdated"

**Risk:** User blindly follows recommendations  
**Mitigation:**
- Prominent disclaimer: "Review with patent attorney"
- Show risk level for each recommendation
- Require explicit confirmation for destructive actions
- Provide detailed reasoning for each recommendation

#### 4.2.8 SECTION G: Patent List Table

**API Response:** Array of patents with scores

**Visual Design:**

```
┌─────────────────────────────────────────────────────────────┐
│ ALL PATENTS (500)                                           │
│                                                             │
│ [Search...] [Filter ▼] [Sort: Filing Date ▼] [Export]     │
│                                                             │
│ Patent No.    Title         Category      Scores    Actions│
│ ────────────────────────────────────────────────────────────│
│ EP1234567B1   Method for..  💎 Hidden Gem  I:48 L:98 [View]│
│                                            F:91 Ft:76       │
│                                                             │
│ EP2345678B1   Apparatus... 👑 Crown Jewel  I:92 L:88 [View]│
│                                            F:78 Ft:85       │
│                                                             │
│ [... 498 more rows ...]                                     │
│                                                             │
│ Showing 1-25 of 500 [< 1 2 3 ... 20 >]                     │
└─────────────────────────────────────────────────────────────┘
```

**Component Structure:**

```tsx
<PatentListTable>
  <TableToolbar>
    <SearchInput
      placeholder="Search patents..."
      onChange={handleSearch}
    />
    <FilterDropdown
      options={filterOptions}
      selected={filters}
      onChange={setFilters}
    />
    <SortDropdown
      options={sortOptions}
      selected={sortBy}
      onChange={setSortBy}
    />
    <Button secondary onClick={exportTable}>Export</Button>
  </TableToolbar>
  
  <Table>
    <TableHead>
      <TableRow>
        <TableHeader sortable onClick={() => sortBy('patent_id')}>
          Patent No.
        </TableHeader>
        <TableHeader sortable onClick={() => sortBy('title')}>
          Title
        </TableHeader>
        <TableHeader sortable onClick={() => sortBy('category')}>
          Category
        </TableHeader>
        <TableHeader>Scores</TableHeader>
        <TableHeader>Actions</TableHeader>
      </TableRow>
    </TableHead>
    
    <TableBody>
      {patents.map(patent => (
        <TableRow key={patent.id} onClick={() => viewPatent(patent.id)}>
          <TableCell>
            <PatentNumber>{patent.id}</PatentNumber>
          </TableCell>
          <TableCell>
            <PatentTitle tooltip={patent.full_title}>
              {truncate(patent.title, 50)}
            </PatentTitle>
          </TableCell>
          <TableCell>
            <CategoryBadge category={patent.category}>
              {getCategoryIcon(patent.category)} {formatCategory(patent.category)}
            </CategoryBadge>
          </TableCell>
          <TableCell>
            <ScoreGrid>
              <Score label="I" value={patent.influence} />
              <Score label="L" value={patent.legal} />
              <Score label="F" value={patent.financial} />
              <Score label="Ft" value={patent.future} />
            </ScoreGrid>
          </TableCell>
          <TableCell>
            <Button small onClick={(e) => {
              e.stopPropagation();
              viewPatent(patent.id);
            }}>
              View
            </Button>
          </TableCell>
        </TableRow>
      ))}
    </TableBody>
  </Table>
  
  <Pagination
    current={page}
    total={Math.ceil(patents.length / pageSize)}
    onChange={setPage}
  />
</PatentListTable>
```

**Interactions:**
- Click row → Open patent detail view
- Click header → Sort by that column
- Type in search → Filter patents
- Select filters → Apply filters
- Click "View" → Navigate to patent page
- Click "Export" → Download CSV/Excel

**Performance Optimization:**

```tsx
// Virtual scrolling for large lists
import { FixedSizeList as List } from 'react-window';

function VirtualizedPatentList({ patents, itemHeight = 60 }) {
  const Row = ({ index, style }) => {
    const patent = patents[index];
    return (
      <div style={style}>
        <PatentRow patent={patent} />
      </div>
    );
  };
  
  return (
    <List
      height={600}
      itemCount={patents.length}
      itemSize={itemHeight}
      width="100%"
    >
      {Row}
    </List>
  );
}
```

**Edge Cases:**
- Empty list → Show "No patents match filters"
- Single patent → Hide pagination
- Very long title → Truncate with tooltip

---

### 4.3 PAGE 3: Search & Discovery

**Route:** `/search`  
**Purpose:** Find patents or companies to analyze

#### 4.3.1 Page Layout

```
┌──────────────────────────────────────────────────────┐
│ HEADER                                                │
├──────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────┐ │
│ │ SECTION A: Hero Search                           │ │
│ │ - Large search input                             │ │
│ │ - Mode selector (Patent / Company)               │ │
│ └──────────────────────────────────────────────────┘ │
│                                                       │
│ ┌──────────────────────────────────────────────────┐ │
│ │ SECTION B: Recent Analyses                       │ │
│ │ - Last 5 analyses with quick access              │ │
│ └──────────────────────────────────────────────────┘ │
│                                                       │
│ ┌──────────────────────────────────────────────────┐ │
│ │ SECTION C: Quick Actions                         │ │
│ │ - Upload CSV                                     │ │
│ │ - Compare Patents                                │ │
│ │ - Portfolio Management                           │ │
│ └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

#### 4.3.2 Hero Search Section

**Visual Design:**

```
┌───────────────────────────────────────────────────────┐
│                                                        │
│                  PatentIQ                              │
│         AI-Powered Patent Portfolio Analysis          │
│                                                        │
│  ( Patent ) ( Company )                               │
│                                                        │
│  ┌──────────────────────────────────────────────────┐│
│  │ Search by patent number or company name...    🔍 ││
│  └──────────────────────────────────────────────────┘│
│                                                        │
│  Examples:                                            │
│  • EP1234567B1                                        │
│  • Siemens AG                                         │
│  • US10123456                                         │
│                                                        │
└───────────────────────────────────────────────────────┘
```

**Component Structure:**

```tsx
<SearchHero>
  <Logo>PatentIQ</Logo>
  <Tagline>AI-Powered Patent Portfolio Analysis</Tagline>
  
  <SearchModeSelector>
    <ModeButton 
      active={mode === 'patent'}
      onClick={() => setMode('patent')}
    >
      Patent
    </ModeButton>
    <ModeButton
      active={mode === 'company'}
      onClick={() => setMode('company')}
    >
      Company
    </ModeButton>
  </SearchModeSelector>
  
  <SearchInput
    large
    placeholder={
      mode === 'patent' 
        ? 'Search by patent number or company name...'
        : 'Search by company name...'
    }
    value={query}
    onChange={setQuery}
    onSubmit={handleSearch}
    icon="🔍"
  />
  
  <SearchExamples>
    <ExampleTitle>Examples:</ExampleTitle>
    {mode === 'patent' ? (
      <>
        <Example onClick={() => search('EP1234567B1')}>• EP1234567B1</Example>
        <Example onClick={() => search('US10123456')}>• US10123456</Example>
      </>
    ) : (
      <>
        <Example onClick={() => search('Siemens AG')}>• Siemens AG</Example>
        <Example onClick={() => search('BMW')}>• BMW</Example>
      </>
    )}
  </SearchExamples>
</SearchHero>
```

**Search Behavior:**

```tsx
function handleSearch(query) {
  // Normalize input
  const normalized = query.trim().toUpperCase();
  
  if (mode === 'patent') {
    // Validate patent format
    if (isValidPatentNumber(normalized)) {
      navigate(`/analyze/${normalized}`);
    } else {
      // Show error
      setError('Invalid patent number format. Try: EP1234567B1');
    }
  } else {
    // Company search
    if (normalized.length < 3) {
      setError('Company name must be at least 3 characters');
      return;
    }
    
    // Navigate to company search results
    navigate(`/portfolio?company=${encodeURIComponent(normalized)}`);
  }
}
```

**Auto-suggestions:**

```tsx
function SearchWithSuggestions() {
  const [suggestions, setSuggestions] = useState([]);
  
  const fetchSuggestions = useDebouncedCallback(async (query) => {
    if (query.length < 3) {
      setSuggestions([]);
      return;
    }
    
    const results = await api.suggest({ query, mode });
    setSuggestions(results);
  }, 300);
  
  return (
    <div className="search-with-suggestions">
      <SearchInput onChange={fetchSuggestions} />
      
      {suggestions.length > 0 && (
        <SuggestionsList>
          {suggestions.map(suggestion => (
            <SuggestionItem
              key={suggestion.id}
              onClick={() => selectSuggestion(suggestion)}
            >
              {suggestion.display}
            </SuggestionItem>
          ))}
        </SuggestionsList>
      )}
    </div>
  );
}
```