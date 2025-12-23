"""
Core module for TrueNAS Sentiment Analysis.
Contains configuration, Claude client, and console output utilities.
"""

from .config import Config, PROJECT_ROOT
from .config import (
    PART1_VERSION, PART2_VERSION, PART3_VERSION, PART4_VERSION, PART5_VERSION,
    LOCAL_VERSION
)
from .console import (
    console,
    print_header,
    print_stage,
    print_progress,
    print_success,
    print_warning,
    print_error,
    print_metric,
    print_divider,
    print_case_progress,
    print_summary_table,
    print_health_score,
    streaming_output,
    StreamingOutput
)
from .claude_client import ClaudeClient, ClaudeResponse, get_claude_client

__all__ = [
    # Config
    'Config',
    'PROJECT_ROOT',
    'PART1_VERSION',
    'PART2_VERSION',
    'PART3_VERSION',
    'PART4_VERSION',
    'PART5_VERSION',
    'LOCAL_VERSION',

    # Console
    'console',
    'print_header',
    'print_stage',
    'print_progress',
    'print_success',
    'print_warning',
    'print_error',
    'print_metric',
    'print_divider',
    'print_case_progress',
    'print_summary_table',
    'print_health_score',
    'streaming_output',
    'StreamingOutput',

    # Claude
    'ClaudeClient',
    'ClaudeResponse',
    'get_claude_client',
]
