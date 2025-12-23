# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered analysis of TrueNAS enterprise support cases. Extracts customer frustration signals, calculates criticality scores, generates account health assessments, and produces interactive dashboards.

## Commands

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Unix

# Run full analysis (Haiku + Sonnet phases)
python -m src.cli analyze input/customer_data.xlsx

# Fast analysis (skip expensive Sonnet phase)
python -m src.cli analyze input/customer_data.xlsx --skip-sonnet

# Launch dashboard (auto-loads most recent analysis)
python -m src.cli dashboard

# Dashboard on custom port with specific analysis
python -m src.cli dashboard --port 8502 --folder outputs/analysis_20251220_001327/

# Validate configuration
python -m src.cli check
```

## Architecture

**Pipeline Flow:**
```
Excel Input → Data Loading → Context Loading → Haiku Analysis → Criticality Scoring → Sonnet Analysis → Visualization → Dashboard
```

**Key Components:**

| Module | Purpose |
|--------|---------|
| `src/cli.py` | Click-based CLI router |
| `src/main.py` | Pipeline orchestrator (`run_analysis()`) |
| `src/analysis/claude_analysis.py` | AI prompting, frustration scoring, timeline generation |
| `src/analysis/scoring.py` | Criticality score calculation, account health formula |
| `src/analysis/data_loader.py` | Excel parsing, duplicate detection |
| `src/context/loader.py` | Product detection, documentation loading |
| `src/core/claude_client.py` | Anthropic API wrapper with retry logic |
| `src/dashboard/app.py` | Streamlit entry point, analysis loading |

**AI Model Usage:**
- **Claude 3.5 Haiku**: Fast bulk analysis - scores every message in every case (0-10 frustration)
- **Claude 3.5 Sonnet**: Quality analysis - detailed timelines for top critical cases only

## Key Algorithms

**Criticality Score** (max 250 pts, in `scoring.py`):
- Claude frustration: 0-100 pts (logarithmic curve)
- Technical severity: S1=35, S2=25, S3=15, S4=5 pts
- Issue class: Systemic=30, Recurring=20, Isolated=10 pts
- Resolution outlook: Challenging=15, Moderate=7, Simple=0 pts
- Support level: Gold=10, Silver=5, Bronze=0 pts
- Plus: message volume, case age, engagement ratio

**Account Health Score** (0-100, in `scoring.py`):
- Higher = healthier
- Thresholds: Critical <40, At Risk <60, Moderate <80, Healthy ≥80

**Product Line Detection** (in `context/loader.py`):
1. Primary: "Product Series" column (F/M/H/R letters)
2. Fallback: Product model patterns (F100-HA, M50, etc.)
3. Last resort: Asset serial prefixes (A1→M-Series, A2→F-Series)

## Important Thresholds

- Sonnet timeline threshold: Cases with criticality ≥125 pts get detailed analysis
- Message history cap: 150K chars for timeline generation
- High frustration: Score ≥7 on 0-10 scale
- Top cases: Always analyze top 25 by criticality

## Output Structure

```
outputs/analysis_YYYYMMDD_HHMMSS/
├── json/
│   ├── summary_statistics.json      # Health score, distributions
│   ├── top_25_critical_cases.json   # Full case data with AI analysis
│   └── all_cases.json               # Condensed case list
└── charts/                          # PNG visualizations
```

## Environment

Requires `.env` with `ANTHROPIC_API_KEY=sk-ant-...`

## Dashboard Pages

1. **Overview** - Health score gauge, key metrics
2. **Cases** - Sortable table with drill-down to AI analysis
3. **Timeline** - Collapsible interaction timelines (Sonnet output)
4. **Trends** - Charts and pattern analysis
5. **Export** - PDF/HTML report generation
