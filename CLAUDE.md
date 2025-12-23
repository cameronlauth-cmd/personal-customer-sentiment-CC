# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Navigate to the app directory first
cd customer-sentiment-analyzer

# Run the Streamlit dashboard
python -m streamlit run app.py

# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_settings.py -v

# Run tests with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing

# Install dependencies
python -m pip install -r requirements.txt
```

## Architecture

### Three-Stage Analysis Pipeline

The system uses a hybrid AI approach combining cost-effective bulk analysis with premium deep analysis:

**Stage 1 - Claude Haiku (All Cases):** Analyzes every message in every case for frustration scoring (0-10), issue classification, and resolution outlook. Fast and cost-effective for high-volume processing.

**Stage 2A - Claude Sonnet (Top 25):** Re-analyzes top-ranked cases for secondary frustration/damage frequency assessment. Adds priority bonus points to criticality scores.

**Stage 2B - Claude Sonnet (Top 10):** Deep timeline analysis with message-level chronology, ownership attribution ([CUSTOMER]/[SUPPORT]), sentiment evolution, and executive summaries.

### Data Flow

```
Excel Upload → DataLoader → Stage 1 (Haiku) → Criticality Scoring → Rank
    → Stage 2A (Sonnet quick) → Re-rank → Stage 2B (Sonnet deep) → Dashboard
```

### Key Components

| File | Purpose |
|------|---------|
| `app.py` | Streamlit entry point, file upload, result persistence |
| `src/sentiment_analyzer.py` | Pipeline orchestrator for 3-stage analysis |
| `src/claude_client.py` | Anthropic API wrapper with retry logic and specialized prompts |
| `src/data_loader.py` | Excel parsing with flexible column mapping, message ownership detection |
| `src/scoring.py` | 8-component criticality formula and account health calculation |
| `config/settings.py` | Models, weights, thresholds, message limits, TrueNAS context prompt |

### Criticality Score Components (~250 max points)

1. Claude frustration (0-100): Base + peak bonus + frequency bonus
2. Severity (5-35): S1=35, S2=25, S3=15, S4=5
3. Issue class (5-30): Systemic=30, Environmental=15, Component=10, Procedural=5
4. Resolution outlook (0-15): Challenging=15, Manageable=8
5. Support level (0-10): Gold=10, Silver=5
6. Message volume (5-30): More messages = prolonged issue
7. Case age (0-10): Older cases prioritized
8. Engagement (0-15): Based on customer response ratio

### Configuration

Environment setup requires `.env` with `ANTHROPIC_API_KEY`.

Model IDs in `config/settings.py`:
- Haiku: `claude-3-5-haiku-latest` (bulk analysis)
- Sonnet: `claude-sonnet-4-20250514` (deep analysis)

Key configurable limits in `config/settings.py`:
- `TIMELINE_MESSAGE_LIMIT`: Max characters for timeline generation (default 300KB)
- `EXECUTIVE_SUMMARY_LIMIT`: Max characters for executive summary input (default 25KB)
- `TOP_QUICK_SCORE`: Number of cases for Stage 2A (default 25)
- `TOP_DETAILED`: Number of cases for Stage 2B timeline (default 10)

The `TRUENAS_CONTEXT` block in settings.py contains enterprise context for proper issue classification - modify this for different domains.

### Message Ownership Detection

`src/data_loader.py` contains `build_enhanced_message_history()` which tags messages as `[CUSTOMER]` or `[SUPPORT]` using heuristic pattern matching and calculates response delays with attribution.

### Dashboard Pages

Multi-page Streamlit app in `pages/`:
- **1_Overview.py**: Open case analysis with customer hotspots and escalation signals
- **2_Cases.py**: Sortable case table with AI summary cards for high-criticality cases
- **3_Timeline.py**: Chronological interaction timelines with frustration highlighting
- **4_Trends.py**: Distribution charts and statistical analysis
- **5_Export.py**: Report generation (CSV, JSON, HTML)

### Data Persistence

Analysis results persist to `data/last_analysis.json` to survive page refreshes. Clear via sidebar button or delete file directly.

### Testing

Tests use pytest with fixtures in `tests/conftest.py`. Current coverage focuses on scoring point functions in `config/settings.py`. Mock API responses for claude_client tests.
