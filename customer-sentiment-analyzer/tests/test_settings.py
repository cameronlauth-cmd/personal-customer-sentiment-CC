"""
Tests for config/settings.py point calculation functions.

These tests demonstrate TDD patterns for the scoring helper functions.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import get_volume_points, get_age_points, get_engagement_points, normalize_case_number


class TestGetVolumePoints:
    """Tests for message volume point calculation."""

    def test_low_volume_returns_5_points(self):
        """Messages <= 5 should return 5 points."""
        assert get_volume_points(1) == 5
        assert get_volume_points(5) == 5

    def test_medium_volume_returns_10_points(self):
        """Messages 6-10 should return 10 points."""
        assert get_volume_points(6) == 10
        assert get_volume_points(10) == 10

    def test_high_volume_returns_20_points(self):
        """Messages 11-20 should return 20 points."""
        assert get_volume_points(11) == 20
        assert get_volume_points(20) == 20

    def test_very_high_volume_returns_30_points(self):
        """Messages > 20 should return 30 points (prolonged issue)."""
        assert get_volume_points(21) == 30
        assert get_volume_points(100) == 30


class TestGetAgePoints:
    """Tests for case age point calculation."""

    def test_very_old_case_returns_10_points(self):
        """Cases >= 90 days should return 10 points."""
        assert get_age_points(90) == 10
        assert get_age_points(180) == 10

    def test_old_case_returns_7_points(self):
        """Cases 60-89 days should return 7 points."""
        assert get_age_points(60) == 7
        assert get_age_points(89) == 7

    def test_moderate_case_returns_5_points(self):
        """Cases 30-59 days should return 5 points."""
        assert get_age_points(30) == 5
        assert get_age_points(59) == 5

    def test_recent_case_returns_3_points(self):
        """Cases 14-29 days should return 3 points."""
        assert get_age_points(14) == 3
        assert get_age_points(29) == 3

    def test_new_case_returns_0_points(self):
        """Cases < 14 days should return 0 points."""
        assert get_age_points(0) == 0
        assert get_age_points(13) == 0


class TestGetEngagementPoints:
    """Tests for customer engagement ratio point calculation."""

    def test_high_engagement_returns_15_points(self):
        """Engagement >= 0.7 should return 15 points."""
        assert get_engagement_points(0.7) == 15
        assert get_engagement_points(1.0) == 15

    def test_medium_engagement_returns_10_points(self):
        """Engagement 0.5-0.69 should return 10 points."""
        assert get_engagement_points(0.5) == 10
        assert get_engagement_points(0.69) == 10

    def test_low_engagement_returns_5_points(self):
        """Engagement 0.3-0.49 should return 5 points."""
        assert get_engagement_points(0.3) == 5
        assert get_engagement_points(0.49) == 5

    def test_very_low_engagement_returns_0_points(self):
        """Engagement < 0.3 should return 0 points."""
        assert get_engagement_points(0.0) == 0
        assert get_engagement_points(0.29) == 0


class TestNormalizeCaseNumber:
    """Tests for case number normalization function."""

    def test_strips_leading_zeros_from_string(self):
        """Leading zeros should be stripped from string case numbers."""
        assert normalize_case_number("00090406") == "90406"
        assert normalize_case_number("00088784") == "88784"
        assert normalize_case_number("000123") == "123"

    def test_handles_integer_input(self):
        """Integer case numbers should be converted to string."""
        assert normalize_case_number(90406) == "90406"
        assert normalize_case_number(123) == "123"

    def test_handles_float_from_pandas(self):
        """Float values (common from pandas) should work correctly."""
        assert normalize_case_number(90406.0) == "90406"
        assert normalize_case_number(123.0) == "123"

    def test_preserves_single_zero(self):
        """Case number '0' should not become empty string."""
        assert normalize_case_number("0") == "0"
        assert normalize_case_number(0) == "0"
        assert normalize_case_number("000") == "0"

    def test_handles_none(self):
        """None should return empty string."""
        assert normalize_case_number(None) == ""

    def test_handles_whitespace(self):
        """Whitespace should be stripped."""
        assert normalize_case_number("  00090406  ") == "90406"
        assert normalize_case_number("  90406") == "90406"

    def test_already_normalized_unchanged(self):
        """Already normalized case numbers should remain unchanged."""
        assert normalize_case_number("90406") == "90406"
        assert normalize_case_number("12345") == "12345"
