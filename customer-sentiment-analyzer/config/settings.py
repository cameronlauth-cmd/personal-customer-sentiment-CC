"""
Configuration settings for Customer Sentiment Analyzer.
Contains model names, scoring weights, and TrueNAS context.
"""

# Model Configuration
# Using current Anthropic model IDs
MODELS = {
    "haiku": "claude-3-5-haiku-latest",
    "sonnet": "claude-sonnet-4-20250514",
}

# API Settings
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds
MAX_TOKENS = 4096

# Analysis Thresholds (legacy - used when cache not provided)
TOP_QUICK_SCORE = 25  # Cases for Stage 2A quick scoring
TOP_DETAILED = 10     # Cases for Stage 2B detailed timeline

# Three-Gate Architecture Thresholds
GATE1_AVG_THRESHOLD = 3           # Avg frustration to trigger Gate 2 (Sonnet quick)
GATE1_PEAK_THRESHOLD = 5          # Peak frustration to trigger Gate 2 (Sonnet quick)
GATE2_CRITICALITY_THRESHOLD = 150 # Criticality score to trigger Gate 3 (timeline)

# Message Limits for API Calls
TIMELINE_MESSAGE_LIMIT = 300000    # 300KB for timeline generation (was 150KB)
EXECUTIVE_SUMMARY_LIMIT = 25000    # 25KB for executive summary generation (was 15KB)

# Cache Configuration for Incremental Analysis
CACHE_FILE = "data/analysis_cache.json"
RECENT_WINDOW_DAYS = 14           # Days to consider as "recent" for trend analysis
TREND_THRESHOLD = 1.5             # Score difference to flag as "declining" or "improving"
HIGH_RECENT_FRUSTRATION = 7.0     # Minimum recent frustration to flag for attention

# Closed Case Status Values (from Salesforce)
CLOSED_STATUSES = [
    "Closed",
    "Closed No Response",
    "Closed Duplicate",
    "Closed Spam",
    "Closed-Test",
    "Closed-NA"
]


def normalize_case_number(case_number) -> str:
    """
    Normalize case number to consistent string format.

    - Strips leading zeros
    - Handles int, float, and string inputs
    - Returns string for consistent dictionary keys

    Examples:
        normalize_case_number("00090406") -> "90406"
        normalize_case_number(90406) -> "90406"
        normalize_case_number(90406.0) -> "90406"
        normalize_case_number("  00090406  ") -> "90406"
    """
    if case_number is None:
        return ""
    # Convert to string, strip whitespace
    case_str = str(case_number).strip()
    # Remove any decimal part (e.g., "90406.0" from pandas)
    if '.' in case_str:
        case_str = case_str.split('.')[0]
    # Strip leading zeros, but keep at least one digit
    return case_str.lstrip('0') or '0'


# Scoring Weights
SEVERITY_WEIGHTS = {
    "S1": 35,
    "S2": 25,
    "S3": 15,
    "S4": 5,
}

ISSUE_CLASS_WEIGHTS = {
    "Systemic": 30,
    "Environmental": 15,
    "Component": 10,
    "Procedural": 5,
    "Unknown": 0,
}

RESOLUTION_WEIGHTS = {
    "Challenging": 15,
    "Manageable": 8,
    "Straightforward": 0,
    "Unknown": 0,
}

SUPPORT_LEVEL_WEIGHTS = {
    "Gold": 10,
    "Silver": 5,
    "Bronze": 0,
    "Unknown": 0,
}

# Message Volume Scoring (more messages = prolonged issue = higher priority)
def get_volume_points(msg_count: int) -> int:
    """Return points based on message count (more = higher priority)."""
    if msg_count <= 5:
        return 5
    elif msg_count <= 10:
        return 10
    elif msg_count <= 20:
        return 20
    else:
        return 30

# Case Age Scoring (longer = higher priority)
def get_age_points(days: int) -> int:
    """Return points based on case age in days."""
    if days >= 90:
        return 10
    elif days >= 60:
        return 7
    elif days >= 30:
        return 5
    elif days >= 14:
        return 3
    else:
        return 0

# Engagement Scoring (graduated scale)
def get_engagement_points(engagement_ratio: float) -> int:
    """Return points based on customer engagement ratio."""
    if engagement_ratio >= 0.7:
        return 15
    elif engagement_ratio >= 0.5:
        return 10
    elif engagement_ratio >= 0.3:
        return 5
    else:
        return 0

# Engagement Threshold (legacy - use get_engagement_points instead)
ENGAGEMENT_THRESHOLD = 0.6
ENGAGEMENT_POINTS = 15

# Frustration Level Thresholds
FRUSTRATION_HIGH = 7
FRUSTRATION_MEDIUM = 4
FRUSTRATION_LOW = 1

# TrueNAS Context for AI Analysis
TRUENAS_CONTEXT = """
COMPANY & PRODUCT CONTEXT:
TrueNAS is an enterprise open-source storage company serving Fortune 500 customers globally.
Products: TrueNAS F-Series (high-performance NVMe), M-Series (high-capacity all-flash/hybrid),
H-Series (versatile & power-efficient), R-Series (single controller appliance).
Technology: ZFS file system, self-healing architecture, unified storage for virtualization and backup.

SUPPORT TIER CONTEXT:
- Gold Support: 24x7 for S1/S2, 4-hour on-site response, proactive monitoring
- Silver Support: 24x5 for S1/S2, next business day on-site response
- Bronze Support: 12x5 business hours, email support, next business day parts

SEVERITY LEVEL DEFINITIONS:
- S1: System not serving data OR severe performance degradation critically disrupting business operations
  → CRITICAL: Production down, data inaccessible, business impact
  → SLA: 2-hour response, 24x7 (Gold/Silver)

- S2: Performance degradation in production OR intermittent faults affecting operations
  → HIGH: System functional but degraded, impacting productivity
  → SLA: 4-hour response, 24x7 (Gold), 24x5 (Silver)

- S3: Issue or defect causing minimal business impact
  → MEDIUM: Minor problems, workarounds available
  → SLA: 4-hour email response during business hours

- S4: Information requests or administrative questions
  → LOW: General inquiries, how-to questions
  → SLA: Next business day response

CUSTOMER PROFILE:
Enterprise B2B customers with mission-critical storage needs. Customers expect:
- Fast response for production issues (S1/S2)
- Expert technical knowledge of ZFS, storage, and enterprise infrastructure
- Professional communication with minimal back-and-forth
- Clear escalation paths and regular updates
- Hardware replacement within SLA commitments

COMMON ISSUES TO RECOGNIZE:
- Storage performance problems (IOPS, latency, throughput)
- Data integrity concerns (scrub errors, disk failures)
- Replication/backup issues affecting disaster recovery
- Hardware failures (drives, controllers, power supplies)
- Software upgrade complications
- Network connectivity or configuration issues

CHURN RISK INDICATORS:
- Threats to switch to competitors (NetApp, Dell EMC, Pure Storage)
- Mentions of contract renewal concerns
- Executive escalation requests
- Repeated issues without resolution
- SLA violations or missed commitments
- Loss of trust in product or support team
"""

# Column Mapping Configuration
COLUMN_MAPPINGS = {
    "case number": ["case number", "case_number", "casenumber", "case no", "case#"],
    "customer name": ["account name", "account_name", "accountname", "customer name",
                      "customer_name", "customername", "customer"],
    "message": ["text body", "text_body", "textbody", "message", "messages",
                "description", "comment", "text", "body"],
    "message date": ["message date", "message_date", "messagedate", "email date",
                     "email_date", "date", "timestamp", "message timestamp"],
    "severity": ["severity", "priority", "level"],
    "support level": ["support level", "support_level", "supportlevel", "tier", "support tier"],
    "created date": ["created date", "created_date", "createddate", "date created",
                     "create date", "opened date"],
    "last modified date": ["last modified date", "last_modified_date", "lastmodifieddate",
                           "modified date", "updated date", "last updated"],
    "status": ["status", "state", "case status"],
    "case age days": ["case age days", "case_age_days", "caseagedays", "age days",
                      "age_days", "agedays", "case age", "case_age"],
}

# Required columns (must be present)
REQUIRED_COLUMNS = ["case number", "customer name", "message", "severity"]

# Optional columns (nice to have)
OPTIONAL_COLUMNS = ["support level", "message date", "created date",
                    "last modified date", "status", "case age days"]
