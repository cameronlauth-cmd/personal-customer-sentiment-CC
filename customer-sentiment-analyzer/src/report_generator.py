"""
HTML report generator using Jinja2 templates.
Generates interactive reports with embedded Plotly charts.
"""

import os
from typing import Dict, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .visualization import create_all_charts, chart_to_html


class ReportGenerationError(Exception):
    """Raised when report generation fails."""
    pass


def get_template_dir() -> str:
    """Get the templates directory path."""
    # Try relative to this file first
    this_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(os.path.dirname(this_dir), "templates")

    if os.path.exists(template_dir):
        return template_dir

    # Try current working directory
    cwd_template = os.path.join(os.getcwd(), "templates")
    if os.path.exists(cwd_template):
        return cwd_template

    # Try parent of current working directory (for Streamlit pages)
    parent_template = os.path.join(os.path.dirname(os.getcwd()), "templates")
    if os.path.exists(parent_template):
        return parent_template

    raise FileNotFoundError("Templates directory not found")


def generate_html_report(
    results: Dict,
    output_path: Optional[str] = None,
    template_name: str = "report.html"
) -> str:
    """Generate HTML report from analysis results.

    Args:
        results: Complete analysis results dictionary
        output_path: Optional path to save the report
        template_name: Name of the template file

    Returns:
        HTML string of the report

    Raises:
        ReportGenerationError: If report generation fails
    """
    # Validate results structure
    if not results:
        raise ReportGenerationError("Results dictionary is empty")

    cases = results.get("cases", [])
    if not cases:
        raise ReportGenerationError("No cases found in results")

    try:
        # Set up Jinja2 environment
        template_dir = get_template_dir()
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

        template = env.get_template(template_name)

        # Generate charts with error handling
        try:
            charts = create_all_charts(results)
            chart_html = {}
            for name, fig in charts.items():
                include_js = (name == "frustration_distribution")
                chart_html[name] = chart_to_html(fig, include_plotlyjs=include_js)
        except Exception as e:
            # Charts failed but we can still generate report without them
            chart_html = {}

        # Ensure statistics structure exists with defaults
        statistics = results.get("statistics", {})
        if "haiku" not in statistics:
            statistics["haiku"] = {
                "high_frustration": 0,
                "avg_frustration_score": 0,
            }
        if "quick_scoring" not in statistics:
            statistics["quick_scoring"] = {"total_scored": 0}
        if "detailed_timeline" not in statistics:
            statistics["detailed_timeline"] = {"total_analyzed": 0}

        # Ensure timing structure exists with defaults
        timing = results.get("timing", {})
        timing.setdefault("haiku_time", 0)
        timing.setdefault("quick_time", 0)
        timing.setdefault("detailed_time", 0)
        timing.setdefault("total_time", 0)

        # Format current date
        current_date = results.get("current_date", datetime.now())
        if isinstance(current_date, datetime):
            date_str = current_date.strftime("%B %d, %Y at %I:%M %p")
        else:
            date_str = str(current_date)

        # Render template
        html = template.render(
            current_date=date_str,
            total_cases=results.get("total_cases", len(cases)),
            cases=cases,
            statistics=statistics,
            distributions=results.get("distributions", {}),
            timing=timing,
            charts=chart_html,
        )

        # Save if path provided
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)

        return html

    except FileNotFoundError as e:
        raise ReportGenerationError(f"Template not found: {e}")
    except Exception as e:
        raise ReportGenerationError(f"Failed to generate report: {e}")


def generate_summary_json(results: Dict) -> Dict:
    """Generate a JSON summary of the analysis results.

    Args:
        results: Complete analysis results dictionary

    Returns:
        Summary dictionary suitable for JSON export
    """
    cases = results.get("cases", [])
    stats = results.get("statistics", {})
    timing = results.get("timing", {})
    distributions = results.get("distributions", {})

    # Build top 25 simplified list
    top_25 = []
    for i, case in enumerate(cases[:25]):
        top_25.append({
            "rank": i + 1,
            "case_number": case.get("case_number"),
            "customer_name": case.get("customer_name"),
            "criticality_score": round(case.get("criticality_score", 0), 1),
            "frustration_score": case.get("claude_analysis", {}).get("frustration_score", 0),
            "issue_class": case.get("claude_analysis", {}).get("issue_class", "Unknown"),
            "resolution_outlook": case.get("claude_analysis", {}).get("resolution_outlook", "Unknown"),
            "severity": case.get("severity", "S4"),
            "support_level": case.get("support_level", "Unknown"),
            "priority": case.get("deepseek_quick_scoring", {}).get("priority", "N/A"),
            "has_detailed_timeline": case.get("deepseek_analysis") is not None,
        })

    # Get current date
    current_date = results.get("current_date", datetime.now())
    if isinstance(current_date, datetime):
        date_str = current_date.strftime("%Y-%m-%d")
    else:
        date_str = str(current_date)

    return {
        "analysis_date": date_str,
        "methodology": "Hybrid: Claude 3.5 Haiku + Claude 3.5 Sonnet",
        "total_cases_analyzed": len(cases),
        "timing": {
            "haiku_analysis_seconds": timing.get("haiku_time", 0),
            "quick_scoring_seconds": timing.get("quick_time", 0),
            "detailed_timeline_seconds": timing.get("detailed_time", 0),
            "total_seconds": timing.get("total_time", 0),
        },
        "frustration_statistics": {
            "high_frustration_cases": stats.get("haiku", {}).get("high_frustration", 0),
            "medium_frustration_cases": stats.get("haiku", {}).get("medium_frustration", 0),
            "low_frustration_cases": stats.get("haiku", {}).get("low_frustration", 0),
            "no_frustration_cases": stats.get("haiku", {}).get("no_frustration", 0),
            "average_frustration_score": stats.get("haiku", {}).get("avg_frustration_score", 0),
        },
        "distributions": {
            "severity": distributions.get("severity", {}),
            "support_level": distributions.get("support_level", {}),
            "issue_classes": distributions.get("issue_classes", {}),
            "resolution_outlooks": distributions.get("resolution_outlooks", {}),
        },
        "top_25_critical_cases": top_25,
    }


def generate_cases_json(results: Dict) -> list:
    """Generate detailed cases JSON for export.

    Args:
        results: Complete analysis results dictionary

    Returns:
        List of case dictionaries
    """
    cases = results.get("cases", [])
    output = []

    for case in cases:
        # Remove DataFrame references that can't be serialized
        case_copy = {
            "case_number": case.get("case_number"),
            "customer_name": case.get("customer_name"),
            "severity": case.get("severity"),
            "support_level": case.get("support_level"),
            "created_date": case.get("created_date"),
            "last_modified_date": case.get("last_modified_date"),
            "status": case.get("status"),
            "case_age_days": case.get("case_age_days"),
            "interaction_count": case.get("interaction_count"),
            "customer_engagement_ratio": case.get("customer_engagement_ratio"),
            "criticality_score": case.get("criticality_score"),
            "score_breakdown": case.get("score_breakdown"),
            "claude_analysis": case.get("claude_analysis"),
            "deepseek_quick_scoring": case.get("deepseek_quick_scoring"),
            "deepseek_analysis": case.get("deepseek_analysis"),
        }
        output.append(case_copy)

    return output
