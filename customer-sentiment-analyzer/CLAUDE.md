# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
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

### Three-Gate Analysis Pipeline

The system uses a threshold-based gate architecture for efficient API cost management:

**Gate 1 - Claude Haiku (All New Messages):** Scores new messages only, updates running avg/peak frustration. Cases pass Gate 1 when: Avg frustration >= 3 OR Peak frustration >= 6.

**Gate 2 - Claude Sonnet Quick (Gate 1 Cases):** Full criticality scoring on cases that passed Gate 1. Cases pass Gate 2 when: Criticality score >= 175. Failed Gate 2 cases have their Sonnet analysis cached for re-evaluation on next upload.

**Gate 3 - Claude Sonnet Timeline (Gate 2 Cases):** Deep timeline analysis with message-level chronology, ownership attribution ([CUSTOMER]/[SUPPORT]), sentiment evolution, and executive summaries. Timelines persist until case closure. New messages append to existing timelines.

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    SCORE REPOSITORY (Cache)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                    New messages uploaded
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GATE 1: HAIKU SCREENING                      │
│  PASS: Avg frustration >= 3 OR Peak frustration >= 6           │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
         GATE 1 FAIL                     GATE 1 PASS
              │                               │
              ▼                               ▼
     Update scores only          ┌────────────────────────────────┐
                                 │      GATE 2: SONNET QUICK      │
                                 │  PASS: Criticality >= 175      │
                                 │  FAIL: Cache, re-eval next     │
                                 └────────────────────────────────┘
                                              │
                              ┌───────────────┴───────────────┐
                         GATE 2 FAIL                     GATE 2 PASS
                              │                               │
                              ▼                               ▼
                    Cache Sonnet result    ┌──────────────────────────────┐
                    Back to pool           │  GATE 3: TIMELINE GENERATION │
                                           │  - New: Generate full timeline│
                                           │  - Existing: Append entries   │
                                           │  - Persist until CLOSED       │
                                           └──────────────────────────────┘
```

### Legacy Mode

When no cache is provided, the system falls back to top-N selection:
- Stage 1: Haiku on all cases
- Stage 2A: Sonnet quick on top 25
- Stage 2B: Sonnet timeline on top 10

### Key Components

| File | Purpose |
|------|---------|
| `app.py` | Streamlit entry point, file upload, result persistence |
| `src/sentiment_analyzer.py` | Pipeline orchestrator for 3-stage analysis |
| `src/claude_client.py` | Anthropic API wrapper with retry logic and specialized prompts |
| `src/data_loader.py` | Excel parsing with flexible column mapping |
| `src/scoring.py` | 8-component criticality formula and account health calculation |
| `config/settings.py` | Models, weights, thresholds, TrueNAS context prompt |

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

The `TRUENAS_CONTEXT` block in settings.py contains enterprise context for proper issue classification - modify this for different domains.

### Dashboard Pages

Multi-page Streamlit app in `pages/`:
- **1_Overview.py**: Open case analysis with customer hotspots and escalation signals
- **2_Cases.py**: Sortable case table with AI summary cards for high-criticality cases
- **3_Timeline.py**: Chronological interaction timelines with frustration highlighting
- **4_Trends.py**: Distribution charts and statistical analysis
- **5_Export.py**: Report generation

### Testing

Tests use pytest with fixtures in `tests/conftest.py`. Current coverage focuses on scoring point functions in `config/settings.py`. Mock API responses for claude_client tests.

### Data Persistence

Analysis results persist to `data/last_analysis.json` to survive page refreshes. Clear via sidebar button or delete file directly.
