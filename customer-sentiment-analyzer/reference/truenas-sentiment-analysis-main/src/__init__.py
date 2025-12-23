"""
TrueNAS Sentiment Analysis - Local Deployment

AI-powered customer sentiment analysis for TrueNAS support cases.
Adapted from Abacus AI workflow for local execution.

Usage:
    python -m src.cli analyze input/salesforce_export.xlsx
"""

from .main import run_analysis
from .core import Config, LOCAL_VERSION

__version__ = LOCAL_VERSION

__all__ = [
    'run_analysis',
    'Config',
    '__version__',
]
