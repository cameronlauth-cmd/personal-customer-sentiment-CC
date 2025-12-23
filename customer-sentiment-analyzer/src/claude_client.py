"""
Anthropic API client wrapper with retry logic for sentiment analysis.
Replaces Abacus AI client with direct Anthropic SDK calls.
Enhanced prompts for business impact detection and detailed timeline generation.
"""

import os
import json
import re
from typing import Optional, Dict, List
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv
import numpy as np
import pandas as pd

# Load environment variables
load_dotenv()

# Import settings
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    MODELS, MAX_RETRIES, RETRY_DELAY, MAX_TOKENS, TRUENAS_CONTEXT,
    TIMELINE_MESSAGE_LIMIT, EXECUTIVE_SUMMARY_LIMIT
)


class ClaudeClient:
    """Wrapper for Anthropic API with retry logic and sentiment analysis methods."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Claude client.

        Args:
            api_key: Optional API key. If not provided, uses ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(api_key=self.api_key)

    def test_connection(self) -> bool:
        """Test the API connection with a simple request."""
        try:
            response = self.client.messages.create(
                model=MODELS["haiku"],
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=RETRY_DELAY, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def _call_api(self, model: str, system: str, prompt: str) -> str:
        """Make an API call with retry logic.

        Args:
            model: Model name to use
            system: System message
            prompt: User prompt

        Returns:
            Response text content
        """
        response = self.client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def analyze_case_messages(
        self,
        case_number: int,
        customer_name: str,
        support_level: str,
        case_age: int,
        interaction_count: int,
        severity: str,
        messages_json: str,
        analysis_context: str = None
    ) -> dict:
        """Stage 1: Analyze case messages with Claude Haiku for frustration scoring.

        Enhanced prompt for business impact and executive mention detection.

        Args:
            case_number: Case identifier
            customer_name: Customer name
            support_level: Support tier (Gold/Silver/Bronze)
            case_age: Age of case in days
            interaction_count: Number of messages
            severity: Severity level (S1-S4)
            messages_json: JSON string of messages to analyze
            analysis_context: Optional context override

        Returns:
            Dictionary with frustration analysis results
        """
        context = analysis_context or TRUENAS_CONTEXT

        # ENHANCED HAIKU PROMPT - Business Impact Detection
        prompt = f"""Analyze EACH message in this support case individually for frustration level.

CASE CONTEXT:
Customer: {customer_name}
Support Level: {support_level} tier
Case Duration: {case_age} days
Total Messages: {interaction_count}
Severity: {severity}

{context}

MESSAGES TO ANALYZE:
{messages_json}

CRITICAL FRUSTRATION SIGNALS TO DETECT:
Watch for these HIGH PRIORITY signals that indicate significant frustration (score 7+):
- Executive mentions: "execs", "management", "leadership", "CEO", "CTO", "board"
- Replacement threats: "replace", "switch", "consider other options", "looking at alternatives"
- Impatience: "impatient", "frustrated", "unacceptable", "too long", "how much longer"
- Trust erosion: "losing confidence", "concerned about", "questioning", "disappointed"
- Business impact: "production", "downtime", "affecting operations", "costing us"
- Escalation: "escalate", "manager", "supervisor", "higher up"
- Ultimatums: "last chance", "final attempt", "if this doesn't work"

SCORING GUIDE (0-10):
- 0: Neutral/positive, thankful, satisfied
- 1-2: Minor concern, patient inquiry, polite follow-up
- 3-4: Some impatience, mild disappointment, timeline concerns
- 5-6: Clear disappointment, repeated issues, patience wearing thin
- 7-8: Frustration visible, executive involvement, questioning value, escalation threats
- 9-10: Extreme anger, trust broken, threats to leave, legal/contract mentions

IMPORTANT: If a message contains EXECUTIVE INVOLVEMENT or REPLACEMENT CONSIDERATIONS, score it 7+ minimum.

Respond with a JSON structure for EACH message:
[
  {{"msg": 1, "score": X, "reason": "brief reason"}},
  {{"msg": 2, "score": Y, "reason": "brief reason"}},
  ...
]

Then provide overall assessment:
ISSUE_CLASS: [What type of problem is this?]
- Systemic: Overall system not meeting performance/reliability expectations
- Environmental: Issues with how system fits in their environment (integration, compatibility)
- Component: Specific hardware/software component problem
- Procedural: Configuration issue, user error, or knowledge gap

RESOLUTION_OUTLOOK: [How likely is permanent resolution?]
- Challenging: May require significant changes or have no clear fix
- Manageable: Can be resolved but may take time/effort
- Straightforward: Clear path to resolution

KEY_PHRASE: [Most concerning customer statement - especially executive mentions or replacement threats]"""

        system = "You are analyzing customer support messages for frustration patterns. Evaluate EACH message independently for emotional signals, then identify overall patterns. Be precise and objective in scoring individual messages."

        try:
            response = self._call_api(MODELS["haiku"], system, prompt)
            return self._parse_haiku_response(response)
        except Exception as e:
            return {
                "frustration_score": 0,
                "frustration_metrics": {
                    "average_score": 0,
                    "peak_score": 0,
                    "frustration_frequency": 0,
                    "frustrated_message_count": 0,
                    "total_messages": 0,
                    "message_scores": []
                },
                "issue_class": "Unknown",
                "resolution_outlook": "Unknown",
                "key_phrase": "",
                "analysis_model": "Claude 3.5 Haiku (Error)",
                "analysis_successful": False,
                "error": str(e)
            }

    def _parse_haiku_response(self, content: str) -> dict:
        """Parse the Haiku analysis response with enhanced hybrid scoring.

        Args:
            content: Raw response content

        Returns:
            Parsed analysis dictionary
        """
        # Parse message scores from JSON response
        message_scores = []
        try:
            json_match = re.search(r'\[.*?\]', content, re.DOTALL)
            if json_match:
                scores_json = json_match.group()
                message_scores = json.loads(scores_json)
        except Exception:
            message_scores = []

        # Calculate metrics with ENHANCED hybrid formula
        if message_scores:
            scores_only = [s.get('score', 0) for s in message_scores]
            average_score = np.mean(scores_only)
            peak_score = max(scores_only)
            frustrated_messages = [s for s in scores_only if s >= 4]
            frustration_frequency = len(frustrated_messages) / len(scores_only)

            # Enhanced hybrid formula - properly weight peak signals
            # Critical insight: Even ONE executive escalation should drive score up
            if peak_score >= 8:
                # Extreme frustration detected - peak dominates
                final_score = (peak_score * 0.8) + (average_score * 0.2)
            elif peak_score >= 7:
                # High frustration signal (executive mention, replacement threat)
                # Don't let low average dilute the score below 5
                final_score = max(5, (peak_score * 0.6) + (average_score * 0.4))
            elif frustration_frequency > 0.5:
                final_score = (peak_score * 0.7) + (average_score * 0.3)
            elif frustration_frequency > 0.2:
                final_score = (peak_score * 0.4) + (average_score * 0.6)
            else:
                # Low frequency but check for any concerning signals
                if peak_score >= 5:
                    final_score = max(3, (peak_score * 0.3) + (average_score * 0.7))
                else:
                    final_score = average_score

            final_score = round(final_score)

            frustration_metrics = {
                'average_score': round(average_score, 2),
                'peak_score': peak_score,
                'frustration_frequency': round(frustration_frequency * 100, 1),
                'frustrated_message_count': len(frustrated_messages),
                'total_messages': len(scores_only),
                'message_scores': message_scores[:10]
            }
        else:
            final_score = 5
            frustration_metrics = {
                'average_score': 5,
                'peak_score': 5,
                'frustration_frequency': 50,
                'frustrated_message_count': 1,
                'total_messages': 0,
                'message_scores': []
            }

        # Parse other fields
        analysis = {
            "frustration_score": min(10, max(0, final_score)),
            "frustration_metrics": frustration_metrics,
            "issue_class": "Procedural",
            "resolution_outlook": "Straightforward",
            "key_phrase": "",
            "analysis_model": "Claude 3.5 Haiku (Hybrid)",
            "analysis_successful": True,
        }

        for line in content.split('\n'):
            line = line.strip()

            if line.startswith('ISSUE_CLASS:'):
                class_text = line.replace('ISSUE_CLASS:', '').strip()
                for cls in ['Systemic', 'Environmental', 'Component', 'Procedural']:
                    if cls in class_text:
                        analysis['issue_class'] = cls
                        break

            elif line.startswith('RESOLUTION_OUTLOOK:'):
                outlook_text = line.replace('RESOLUTION_OUTLOOK:', '').strip()
                for outlook in ['Challenging', 'Manageable', 'Straightforward']:
                    if outlook in outlook_text:
                        analysis['resolution_outlook'] = outlook
                        break

            elif line.startswith('KEY_PHRASE:'):
                phrase = line.replace('KEY_PHRASE:', '').strip()
                if phrase.lower() != "none":
                    analysis['key_phrase'] = phrase.strip('"').strip("'")

        return analysis

    def quick_score(
        self,
        case: dict,
        analysis_context: str = None
    ) -> dict:
        """Stage 2A: Quick scoring with Claude Sonnet for top cases.

        Enhanced prompt that includes key phrase from initial analysis
        and critical signals detection.

        Args:
            case: Case dictionary with analysis data
            analysis_context: Optional context override

        Returns:
            Quick scoring results
        """
        context = analysis_context or TRUENAS_CONTEXT
        messages = case.get('messages_full', '')
        haiku_analysis = case.get('claude_analysis', {})
        key_phrase = haiku_analysis.get('key_phrase', '')
        peak_score = haiku_analysis.get('frustration_metrics', {}).get('peak_score', 0)

        # Smart message truncation - include both beginning and end for high-frustration cases
        if peak_score >= 7 and len(messages) > 12000:
            messages_for_analysis = messages[:6000] + "\n\n[...middle messages omitted...]\n\n" + messages[-6000:]
        else:
            messages_for_analysis = messages[:12000]

        # ENHANCED SONNET QUICK SCORING PROMPT
        prompt = f"""Assess this customer support case for prioritization scoring.

CASE OVERVIEW:
Customer: {case.get('customer_name', 'Unknown')}
Support Level: {case.get('support_level', 'Unknown')}
Duration: {case.get('case_age_days', 0)} days
Messages: {case.get('interaction_count', 0)}
Initial Frustration Score: {haiku_analysis.get('frustration_score', 0)}/10
Peak Frustration Detected: {peak_score}/10
Severity: {case.get('severity', 'S4')}

KEY PHRASE DETECTED BY INITIAL ANALYSIS:
"{key_phrase}"

{context}

CRITICAL SIGNALS TO WATCH FOR:
- Executive involvement: "execs", "management", "CEO", "CTO", "board"
- Replacement threats: "replace", "switch", "consider alternatives"
- Trust erosion: "losing confidence", "disappointed", "concerned"
- Business impact: "production", "downtime", "costing us"

MESSAGE HISTORY (chronological):
{messages_for_analysis}

SCORING ASSESSMENT:
Based on patterns in the messages AND the key phrase detected, provide:

FRUSTRATION_FREQUENCY: [What % of messages show customer frustration? 0-100]
RELATIONSHIP_DAMAGE_FREQUENCY: [What % of interactions damaged confidence? 0-100]
CUSTOMER_PRIORITY: [Critical/High/Medium/Low based on relationship risk]
JUSTIFICATION: [2-3 sentences explaining priority level]

IMPORTANT: If the key phrase mentions executives, replacement, or impatience, score FRUSTRATION_FREQUENCY at 20+ and mark as High/Critical priority."""

        system = "You are analyzing customer support cases for prioritization. Focus on identifying patterns and risk levels efficiently. Maintain objective, factual language."

        try:
            response = self._call_api(MODELS["sonnet"], system, prompt)
            return self._parse_quick_score_response(response)
        except Exception as e:
            return {
                'frustration_frequency': 0,
                'damage_frequency': 0,
                'priority': 'Medium',
                'justification': f'Scoring failed: {str(e)}',
                'analysis_model': 'Claude 3.5 Sonnet (Error)',
                'analysis_successful': False
            }

    def _parse_quick_score_response(self, content: str) -> dict:
        """Parse quick score response."""
        scoring = {
            'frustration_frequency': 0,
            'damage_frequency': 0,
            'priority': 'Medium',
            'justification': '',
            'analysis_model': 'Claude 3.5 Sonnet Quick Scoring',
            'analysis_successful': True
        }

        for line in content.split('\n'):
            line_stripped = line.strip()
            if 'FRUSTRATION_FREQUENCY:' in line_stripped:
                nums = [int(s) for s in line_stripped.split() if s.isdigit()]
                if nums:
                    scoring['frustration_frequency'] = min(100, max(0, nums[0]))
            elif 'RELATIONSHIP_DAMAGE_FREQUENCY:' in line_stripped:
                nums = [int(s) for s in line_stripped.split() if s.isdigit()]
                if nums:
                    scoring['damage_frequency'] = min(100, max(0, nums[0]))
            elif 'CUSTOMER_PRIORITY:' in line_stripped:
                for priority in ['Critical', 'High', 'Medium', 'Low']:
                    if priority in line_stripped:
                        scoring['priority'] = priority
                        break
            elif 'JUSTIFICATION:' in line_stripped:
                scoring['justification'] = line_stripped.split(':', 1)[1].strip() if ':' in line_stripped else ''

        return scoring

    def deep_timeline(
        self,
        case: dict,
        case_data: pd.DataFrame = None,
        analysis_context: str = None
    ) -> dict:
        """Stage 2B: Deep timeline analysis with Claude Sonnet for top cases.

        Two-step approach:
        1. Generate detailed chronological timeline with ownership attribution
        2. Generate executive summary from timeline

        Args:
            case: Case dictionary with all data
            case_data: DataFrame with case messages (optional, falls back to case['case_data'])
            analysis_context: Optional context override

        Returns:
            Detailed timeline analysis with executive summary
        """
        context = analysis_context or TRUENAS_CONTEXT

        # Get case data DataFrame
        if case_data is None:
            case_data = case.get('case_data')
        if case_data is None or case_data.empty:
            return {
                "timeline_entries": [],
                "executive_summary": "No message data available",
                "pain_points": "",
                "sentiment_trend": "Unknown",
                "critical_inflection_points": "",
                "customer_priority": "Medium",
                "recommended_action": "Manual review required",
                "analysis_model": "Claude 3.5 Sonnet (No Data)",
                "analysis_successful": False
            }

        # Import build_enhanced_message_history from data_loader
        from src.data_loader import build_enhanced_message_history

        # Build enhanced message history with [CUSTOMER]/[SUPPORT] attribution
        enhanced_message_history = build_enhanced_message_history(case_data)

        # Truncate if too long (configurable limit to capture all messages)
        if len(enhanced_message_history) > TIMELINE_MESSAGE_LIMIT:
            enhanced_message_history = enhanced_message_history[:TIMELINE_MESSAGE_LIMIT] + "\n\n[...additional messages truncated...]"

        # STEP 1: ENHANCED TIMELINE PROMPT
        timeline_prompt = f"""Analyze this customer support case to assess relationship health and identify areas requiring attention.

CASE OVERVIEW:
Customer: {case.get('customer_name', 'Unknown')}
Support Level: {case.get('support_level', 'Unknown')}
Issue Severity: {case.get('severity', 'S4')}
Case Status: {case.get('status', 'Unknown')}
Case Duration: {case.get('case_age_days', 0)} days
Message Count: {case.get('interaction_count', 0)} messages
Initial Assessment: {case.get('claude_analysis', {}).get('frustration_score', 0)}/10 frustration score

{context}

RESPONSE OWNERSHIP CONTEXT (CRITICAL):
Each message below is marked with [CUSTOMER] or [SUPPORT] and includes delay attribution.

INTERPRETING DELAYS:
- "(Xd delay - SUPPORT responsible)" = Customer sent last message, we took X days to respond
  -> This IS a support quality issue if it violates SLA (S1 = same day, S2 = next business day)

- "(Xd delay - CUSTOMER not responding)" = We sent last message, customer took X days to respond
  -> This is NOT a support quality issue - customer is not engaging
  -> Multiple support follow-ups to silent customer = PROACTIVE support (POSITIVE)
  -> Do NOT penalize support for customer non-responsiveness

COMPLETE MESSAGE HISTORY (chronological with ownership):
{enhanced_message_history}

ANALYSIS REQUIREMENTS:

Create a DETAILED chronological timeline covering ALL messages. Use FINE GRANULARITY:
- Group routine messages in small batches (2-8 messages per group)
- Use SINGLE MESSAGE entries for any critical moment: escalations, outages, frustration spikes, executive mentions, failures, resolutions
- A 95-message case should have 15-25+ timeline entries, NOT 5-10

CRITICAL MOMENTS requiring individual Message entries:
- Production outages or incidents
- Executive escalation or mentions ("execs", "management", "CEO")
- Hardware replacement discussions
- Failed remediation attempts
- Customer expressing anxiety, fear, or strong frustration
- Major tone shifts
- Resolution milestones

For each timeline entry, use this format:

TIMELINE_ENTRY: [Messages X-Y - Date: MMM DD-DD, YYYY] OR [Message X - Date: MMM DD, YYYY]
SUMMARY: [Detailed factual description - include specific technical details and customer quotes]
CUSTOMER_TONE: [Observed tone - be specific: "Professional, cooperative", "Anxious, seeking reassurance", "Alarmed, managing crisis"]
FRUSTRATION_DETECTED: [Yes/No]
FRUSTRATION_DETAIL: [If yes: Include the EXACT customer quote in quotation marks]
POSITIVE_ACTION_DETECTED: [Yes/No]
POSITIVE_ACTION_DETAIL: [If yes: Include specific quote or action]
SUPPORT_QUALITY: [Assessment with specifics]
RELATIONSHIP_IMPACT: [Effect on customer confidence]
FAILURE_PATTERN_DETECTED: [Yes/No]
FAILURE_PATTERN_DETAIL: [If yes: Show the CHAIN/SEQUENCE of failures]
ANALYSIS: [For critical moments only - key insight about this interaction]

IMPORTANT RULES:
1. Include EXACT customer quotes in quotation marks for frustration and positive actions
2. Track failure patterns as CHAINS showing progression
3. Single-message entries for ANY executive mention, outage, or major escalation
4. Cover ALL messages - verify your last entry includes the final messages
5. For long cases (50+ messages), you MUST have 15+ timeline entries

Base all statements strictly on what appears in the messages. Direct quotes must be verbatim."""

        system = "You are an enterprise customer experience analyst providing objective assessments of support interactions. Your role is to identify patterns, assess relationship health, and provide actionable insights. Maintain a professional, analytical tone suitable for executive review."

        try:
            # Step 1: Generate timeline
            timeline_response = self._call_api(MODELS["sonnet"], system, timeline_prompt)

            # DEBUG: Save raw response to file for troubleshooting
            from pathlib import Path
            debug_dir = Path(__file__).parent.parent / "data" / "debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_file = debug_dir / f"timeline_response_{case.get('case_number', 'unknown')}.txt"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(timeline_response)

            timeline_entries = self._parse_timeline_entries(timeline_response, case_data)

            # Step 2: Generate executive summary from timeline
            if timeline_entries:
                summary = self._generate_executive_summary(case, timeline_entries, context)
            else:
                summary = {}

            return {
                "timeline_entries": timeline_entries,
                "executive_summary": summary.get('executive_summary', ''),
                "pain_points": summary.get('pain_points', ''),
                "sentiment_trend": summary.get('sentiment_trend', ''),
                "critical_inflection_points": summary.get('critical_inflection_points', ''),
                "customer_priority": summary.get('customer_priority', 'Medium'),
                "recommended_action": summary.get('recommended_action', ''),
                "root_cause": summary.get('root_cause', ''),
                "analysis_model": "Claude 3.5 Sonnet",
                "analysis_successful": True,
                "raw_timeline_response": timeline_response
            }
        except Exception as e:
            return {
                "timeline_entries": [],
                "executive_summary": f"Analysis failed: {str(e)}",
                "pain_points": "Analysis failed",
                "sentiment_trend": "Unknown",
                "critical_inflection_points": "",
                "customer_priority": "Medium",
                "recommended_action": "Manual review required",
                "root_cause": f"Analysis error: {str(e)}",
                "analysis_model": "Claude 3.5 Sonnet (Error)",
                "analysis_successful": False
            }

    def _parse_timeline_entries(self, content: str, case_data: pd.DataFrame = None) -> list:
        """Parse timeline entries from response with multi-line field support.

        Args:
            content: Raw timeline response
            case_data: DataFrame with case messages for excerpt extraction

        Returns:
            List of timeline entry dictionaries
        """
        lines = content.split('\n')
        timeline_entries = []
        current_entry = None
        current_field = None  # Track which field we're accumulating content for

        field_markers = {
            'SUMMARY': 'summary',
            'CUSTOMER_TONE': 'customer_tone',
            'CUSTOMER TONE': 'customer_tone',
            'FRUSTRATION_DETECTED': 'frustration_detected',
            'FRUSTRATION DETECTED': 'frustration_detected',
            'FRUSTRATION_DETAIL': 'frustration_detail',
            'FRUSTRATION DETAIL': 'frustration_detail',
            'POSITIVE_ACTION_DETECTED': 'positive_action_detected',
            'POSITIVE ACTION DETECTED': 'positive_action_detected',
            'POSITIVE_ACTION_DETAIL': 'positive_action_detail',
            'POSITIVE ACTION DETAIL': 'positive_action_detail',
            'SUPPORT_QUALITY': 'support_quality',
            'SUPPORT QUALITY': 'support_quality',
            'RELATIONSHIP_IMPACT': 'relationship_impact',
            'RELATIONSHIP IMPACT': 'relationship_impact',
            'FAILURE_PATTERN_DETECTED': 'failure_pattern_detected',
            'FAILURE PATTERN DETECTED': 'failure_pattern_detected',
            'FAILURE_PATTERN_DETAIL': 'failure_pattern_detail',
            'FAILURE PATTERN DETAIL': 'failure_pattern_detail',
            'ANALYSIS': 'analysis',
        }

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # Clean markdown formatting
            line_cleaned = line_stripped.replace('**', '').replace('###', '').replace('##', '').replace('---', '').strip()
            if not line_cleaned:
                continue

            # Check for new timeline entry
            if 'TIMELINE_ENTRY' in line_cleaned.upper():
                if current_entry and current_entry.get('entry_label'):
                    timeline_entries.append(current_entry)

                # Extract entry label
                entry_label = 'Unknown'
                if ':' in line_cleaned:
                    parts = line_cleaned.split(':', 1)
                    if len(parts) > 1:
                        entry_label = parts[1].strip().strip('[]')

                current_entry = {
                    'entry_label': entry_label,
                    'summary': '',
                    'customer_tone': '',
                    'frustration_detected': '',
                    'frustration_detail': '',
                    'positive_action_detected': '',
                    'positive_action_detail': '',
                    'support_quality': '',
                    'relationship_impact': '',
                    'failure_pattern_detected': '',
                    'failure_pattern_detail': '',
                    'analysis': '',
                    'message_excerpt': None,
                    'positive_excerpt': None,
                }
                current_field = None
                continue

            if current_entry is not None:
                # Check if this line starts a new field
                field_found = False
                for marker, field in field_markers.items():
                    line_upper = line_cleaned.upper()
                    if line_upper.startswith(marker):
                        field_found = True
                        current_field = field
                        # Extract content after the marker
                        content_after = ''
                        if ':' in line_cleaned:
                            content_after = line_cleaned.split(':', 1)[1].strip()
                        current_entry[field] = content_after
                        break

                # If no new field marker and we have a current field, append content
                if not field_found and current_field and line_cleaned:
                    existing = current_entry.get(current_field, '')
                    if existing:
                        current_entry[current_field] = existing + ' ' + line_cleaned
                    else:
                        current_entry[current_field] = line_cleaned

        if current_entry and current_entry.get('entry_label'):
            timeline_entries.append(current_entry)

        # Extract message excerpts if case_data is available
        if case_data is not None and not case_data.empty:
            self._extract_message_excerpts(timeline_entries, case_data)

        return timeline_entries

    def _extract_message_excerpts(self, timeline_entries: list, case_data: pd.DataFrame):
        """Extract and highlight message excerpts for timeline entries.

        Args:
            timeline_entries: List of timeline entries to update
            case_data: DataFrame with case messages
        """
        case_data_sorted = case_data.sort_values('Message Date')
        messages_list = case_data_sorted["Message"].tolist()

        for entry in timeline_entries:
            # Extract frustrated excerpts
            frustration_detail = entry.get('frustration_detail', '')
            quoted_text = re.findall(r'"([^"]+)"', frustration_detail)
            if not quoted_text:
                quoted_text = re.findall(r"'([^']+)'", frustration_detail)

            if quoted_text and len(quoted_text[0]) > 10:
                frustrated_quote = quoted_text[0]
                quote_lower = frustrated_quote.lower()

                for msg in messages_list:
                    if pd.isna(msg):
                        continue
                    msg_str = str(msg).strip()
                    msg_lower = msg_str.lower()

                    if quote_lower in msg_lower:
                        quote_pos = msg_lower.find(quote_lower)
                        start = max(0, quote_pos - 200)
                        end = min(len(msg_str), quote_pos + len(frustrated_quote) + 200)

                        excerpt_text = msg_str[start:end].strip()
                        if start > 0:
                            excerpt_text = "..." + excerpt_text
                        if end < len(msg_str):
                            excerpt_text = excerpt_text + "..."

                        # HTML escape
                        excerpt_text = excerpt_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        escaped_quote = frustrated_quote.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

                        excerpt_lower = excerpt_text.lower()
                        escaped_quote_lower = escaped_quote.lower()
                        quote_start = excerpt_lower.find(escaped_quote_lower)

                        if quote_start != -1:
                            before = excerpt_text[:quote_start]
                            matched = excerpt_text[quote_start:quote_start + len(escaped_quote)]
                            after = excerpt_text[quote_start + len(escaped_quote):]

                            frustration_detected = entry.get('frustration_detected', '').lower()
                            color = '#DC2626' if 'yes' in frustration_detected else '#ea580c'

                            entry['message_excerpt'] = f'{before}<font color="{color}"><b>{matched}</b></font>{after}'
                        else:
                            entry['message_excerpt'] = excerpt_text
                        break

            # Extract positive excerpts
            positive_detail = entry.get('positive_action_detail', '')
            quoted_text = re.findall(r'"([^"]+)"', positive_detail)
            if not quoted_text:
                quoted_text = re.findall(r"'([^']+)'", positive_detail)

            if quoted_text and len(quoted_text[0]) > 10:
                positive_quote = quoted_text[0]
                quote_lower = positive_quote.lower()

                for msg in messages_list:
                    if pd.isna(msg):
                        continue
                    msg_str = str(msg).strip()
                    msg_lower = msg_str.lower()

                    if quote_lower in msg_lower:
                        quote_pos = msg_lower.find(quote_lower)
                        start = max(0, quote_pos - 200)
                        end = min(len(msg_str), quote_pos + len(positive_quote) + 200)

                        excerpt_text = msg_str[start:end].strip()
                        if start > 0:
                            excerpt_text = "..." + excerpt_text
                        if end < len(msg_str):
                            excerpt_text = excerpt_text + "..."

                        excerpt_text = excerpt_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        escaped_quote = positive_quote.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

                        excerpt_lower = excerpt_text.lower()
                        escaped_quote_lower = escaped_quote.lower()
                        quote_start = excerpt_lower.find(escaped_quote_lower)

                        if quote_start != -1:
                            before = excerpt_text[:quote_start]
                            matched = excerpt_text[quote_start:quote_start + len(escaped_quote)]
                            after = excerpt_text[quote_start + len(escaped_quote):]

                            entry['positive_excerpt'] = f'{before}<font color="#16a34a"><b>{matched}</b></font>{after}'
                        else:
                            entry['positive_excerpt'] = excerpt_text
                        break

    def _generate_executive_summary(self, case: dict, timeline_entries: list, context: str) -> dict:
        """Generate executive summary from timeline.

        Args:
            case: Case dictionary
            timeline_entries: List of parsed timeline entries
            context: Analysis context

        Returns:
            Executive summary dictionary
        """
        # Build timeline summary for the prompt
        timeline_summary = "\n\n".join([
            f"TIMELINE_ENTRY: {entry.get('entry_label', 'Unknown')}\n"
            f"Summary: {entry.get('summary', 'N/A')}\n"
            f"Customer Tone: {entry.get('customer_tone', 'N/A')}\n"
            f"Frustration: {entry.get('frustration_detected', 'N/A')} - {entry.get('frustration_detail', '')}\n"
            f"Failure Pattern: {entry.get('failure_pattern_detected', 'N/A')} - {entry.get('failure_pattern_detail', '')}"
            for entry in timeline_entries
        ])

        if len(timeline_summary) > EXECUTIVE_SUMMARY_LIMIT:
            timeline_summary = timeline_summary[:EXECUTIVE_SUMMARY_LIMIT] + "\n\n[...truncated...]"

        summary_prompt = f"""Based on the chronological timeline analysis of this support case, provide an executive summary.

CASE CONTEXT:
Customer: {case.get('customer_name', 'Unknown')}
Support Level: {case.get('support_level', 'Unknown')}
Issue Severity: {case.get('severity', 'S4')}
Case Status: {case.get('status', 'Unknown')}
Case Duration: {case.get('case_age_days', 0)} days
Total Messages: {case.get('interaction_count', 0)}

TIMELINE ANALYSIS:
{timeline_summary}

Provide executive summary using the exact format below:

EXECUTIVE_SUMMARY: [2-3 sentence synthesis for an executive with no context: What happened, current relationship state, and what needs to happen next.]
PAIN_POINTS: [Key customer concerns based on communication patterns - 2-3 sentences]
SENTIMENT_TREND: [Evolution of customer sentiment throughout interaction - 1-2 sentences]
CRITICAL_INFLECTION_POINTS: [2-3 specific moments where relationship trajectory changed]
CUSTOMER_PRIORITY: [Urgency level based on analysis: Critical/High/Medium/Low]
RECOMMENDED_ACTION: [Specific next action to advance or resolve the case - 1-2 sentences]

Base your assessment on the timeline patterns identified above."""

        system = "You are an enterprise customer experience analyst providing executive insights. Identify patterns, assess relationship health, and provide actionable recommendations."

        try:
            response = self._call_api(MODELS["sonnet"], system, summary_prompt)
            return self._parse_executive_summary(response)
        except Exception:
            return {}

    def _parse_executive_summary(self, content: str) -> dict:
        """Parse executive summary fields with multi-line support.

        Args:
            content: Raw summary response

        Returns:
            Parsed summary dictionary
        """
        summary = {
            'executive_summary': '',
            'pain_points': '',
            'sentiment_trend': '',
            'critical_inflection_points': '',
            'customer_priority': 'Medium',
            'recommended_action': '',
            'root_cause': ''
        }

        lines = content.split('\n')
        current_field = None
        field_content = []

        field_markers = {
            'EXECUTIVE_SUMMARY:': 'executive_summary',
            'EXECUTIVE SUMMARY:': 'executive_summary',
            'PAIN_POINTS:': 'pain_points',
            'PAIN POINTS:': 'pain_points',
            'SENTIMENT_TREND:': 'sentiment_trend',
            'SENTIMENT TREND:': 'sentiment_trend',
            'CRITICAL_INFLECTION_POINTS:': 'critical_inflection_points',
            'CRITICAL INFLECTION POINTS:': 'critical_inflection_points',
            'CUSTOMER_PRIORITY:': 'customer_priority',
            'CUSTOMER PRIORITY:': 'customer_priority',
            'RECOMMENDED_ACTION:': 'recommended_action',
            'RECOMMENDED ACTION:': 'recommended_action',
            'ROOT_CAUSE:': 'root_cause',
            'ROOT CAUSE:': 'root_cause',
        }

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            line_cleaned = line_stripped.replace('**', '').replace('###', '').replace('##', '').strip()

            # Check for field markers
            matched_field = None
            for marker, field in field_markers.items():
                if marker in line_cleaned.upper():
                    matched_field = field
                    break

            if matched_field:
                if current_field and field_content:
                    summary[current_field] = ' '.join(field_content).strip()

                current_field = matched_field
                after_colon = line_cleaned.split(':', 1)[1].strip() if ':' in line_cleaned else ''

                if matched_field == 'customer_priority':
                    for priority in ['Critical', 'High', 'Medium', 'Low']:
                        if priority in after_colon:
                            summary['customer_priority'] = priority
                            break
                    current_field = None
                    field_content = []
                else:
                    field_content = [after_colon] if after_colon else []
            elif current_field and line_cleaned:
                field_content.append(line_stripped.lstrip('-*-> '))

        if current_field and field_content:
            summary[current_field] = ' '.join(field_content).strip()

        return summary
