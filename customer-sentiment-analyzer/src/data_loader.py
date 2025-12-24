"""
Excel data loader with flexible column mapping.
Handles various column naming conventions from TrueNAS exports.
"""

import io
from datetime import datetime
from typing import Tuple, Dict, Optional, BinaryIO, Union
import pandas as pd

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import COLUMN_MAPPINGS, REQUIRED_COLUMNS, OPTIONAL_COLUMNS, normalize_case_number


class DataLoader:
    """Load and prepare Excel data for sentiment analysis."""

    def __init__(self):
        """Initialize the data loader."""
        self.column_mapping = COLUMN_MAPPINGS
        self.required_columns = REQUIRED_COLUMNS
        self.optional_columns = OPTIONAL_COLUMNS
        self.current_date = datetime.now()

    def load_excel(
        self,
        file: Union[str, BinaryIO, bytes],
        sheet_name: Optional[str] = None
    ) -> Tuple[pd.DataFrame, datetime]:
        """Load Excel file and prepare dataframe.

        Args:
            file: File path, file object, or bytes
            sheet_name: Optional sheet name to load

        Returns:
            Tuple of (prepared DataFrame, current date)

        Raises:
            ValueError: If required columns are missing or file cannot be loaded
        """
        # Load the Excel file
        df = self._read_excel(file, sheet_name)

        # Clean column names
        df.columns = df.columns.str.strip()

        # Map columns to standard names
        df = self._map_columns(df)

        # Clean and validate data
        df = self._clean_data(df)

        return df, self.current_date

    def _read_excel(
        self,
        file: Union[str, BinaryIO, bytes],
        sheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """Read Excel file with fallback engines."""
        kwargs = {"sheet_name": sheet_name} if sheet_name else {}

        # Handle different input types
        if isinstance(file, bytes):
            file = io.BytesIO(file)
        elif hasattr(file, 'read'):
            # File-like object from Streamlit
            file = io.BytesIO(file.read())

        try:
            return pd.read_excel(file, engine="openpyxl", **kwargs)
        except Exception as e:
            try:
                if hasattr(file, 'seek'):
                    file.seek(0)
                return pd.read_excel(file, engine="xlrd", **kwargs)
            except Exception as e2:
                raise ValueError(f"Failed to load Excel file: {str(e)}")

    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map various column names to standard names.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with standardized column names
        """
        # Create lowercase mapping
        column_lower = {col.lower(): col for col in df.columns}

        # Find actual column names for each required/optional field
        actual_columns = {}

        for standard_name, possible_names in self.column_mapping.items():
            found = False

            # First try exact match
            for possible_name in possible_names:
                if possible_name in column_lower:
                    actual_columns[standard_name] = column_lower[possible_name]
                    found = True
                    break

            # Then try partial match
            if not found:
                for col_lower, col_actual in column_lower.items():
                    if any(pn in col_lower for pn in possible_names):
                        actual_columns[standard_name] = col_actual
                        found = True
                        break

            # Check if required column is missing
            if not found and standard_name in self.required_columns:
                raise ValueError(
                    f"Missing required column: {standard_name}. "
                    f"Available columns: {list(df.columns)}"
                )

        # Build rename dictionary
        rename_dict = {
            actual_columns["case number"]: "Case Number",
            actual_columns["customer name"]: "Customer Name",
            actual_columns["message"]: "Message",
            actual_columns["severity"]: "Severity",
        }

        # Add optional columns if found
        optional_mapping = {
            "support level": "Support Level",
            "message date": "Message Date",
            "created date": "Created Date",
            "last modified date": "Last Modified Date",
            "case age days": "Case Age Days",
            "status": "Status",
        }

        for key, standard in optional_mapping.items():
            if key in actual_columns:
                rename_dict[actual_columns[key]] = standard

        return df.rename(columns=rename_dict)

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate the data.

        Args:
            df: DataFrame with standardized columns

        Returns:
            Cleaned DataFrame
        """
        # Drop rows with missing required data
        df = df.dropna(subset=["Case Number", "Message"])

        # Fill missing optional fields
        df["Customer Name"] = df["Customer Name"].fillna("Unknown Customer")
        df["Severity"] = df["Severity"].fillna("S4")

        # Handle Support Level
        if "Support Level" not in df.columns:
            df["Support Level"] = "Unknown"
        else:
            df["Support Level"] = df["Support Level"].fillna("Unknown")

        # Handle dates
        df = self._process_dates(df)

        # Handle Case Age
        df = self._calculate_case_age(df)

        # Handle Status
        if "Status" not in df.columns:
            df["Status"] = "Unknown"
        else:
            df["Status"] = df["Status"].fillna("Unknown")

        # Normalize severity
        df["Severity"] = df["Severity"].apply(self._extract_severity)

        # Normalize support level
        df["Support Level"] = df["Support Level"].apply(self._extract_support_level)

        return df

    def _process_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process date columns."""
        # Message Date
        if "Message Date" in df.columns:
            try:
                df["Message Date"] = pd.to_datetime(df["Message Date"], errors="coerce")
            except Exception:
                df["Message Date"] = pd.NaT
            df["Message Date"] = df["Message Date"].fillna(self.current_date)
        else:
            if "Created Date" in df.columns:
                df["Message Date"] = df["Created Date"]
            else:
                df["Message Date"] = self.current_date

        # Created Date
        if "Created Date" in df.columns:
            try:
                df["Created Date"] = pd.to_datetime(df["Created Date"], errors="coerce")
            except Exception:
                df["Created Date"] = pd.NaT
            df["Created Date"] = df["Created Date"].fillna(self.current_date)
        else:
            df["Created Date"] = self.current_date

        # Last Modified Date
        if "Last Modified Date" in df.columns:
            try:
                df["Last Modified Date"] = pd.to_datetime(df["Last Modified Date"], errors="coerce")
            except Exception:
                df["Last Modified Date"] = pd.NaT
            df["Last Modified Date"] = df["Last Modified Date"].fillna(self.current_date)
        else:
            df["Last Modified Date"] = self.current_date

        return df

    def _calculate_case_age(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate or use case age in days."""
        if "Case Age Days" in df.columns:
            df["case_age_days"] = pd.to_numeric(
                df["Case Age Days"], errors="coerce"
            ).fillna(0).astype(int)
        else:
            df["case_age_days"] = (self.current_date - df["Created Date"]).dt.days
            df["case_age_days"] = df["case_age_days"].fillna(0).astype(int)

        return df

    @staticmethod
    def _extract_severity(severity_str: str) -> str:
        """Extract severity level from string."""
        severity_str = str(severity_str).upper()
        if "S1" in severity_str:
            return "S1"
        elif "S2" in severity_str:
            return "S2"
        elif "S3" in severity_str:
            return "S3"
        elif "S4" in severity_str:
            return "S4"
        else:
            return "S4"

    @staticmethod
    def _extract_support_level(support_str: str) -> str:
        """Extract support level from string."""
        support_str = str(support_str).upper()
        if "GOLD" in support_str:
            return "Gold"
        elif "SILVER" in support_str:
            return "Silver"
        elif "BRONZE" in support_str:
            return "Bronze"
        else:
            return "Unknown"

    def get_unique_cases(self, df: pd.DataFrame) -> list:
        """Get list of unique case numbers.

        Args:
            df: DataFrame with case data

        Returns:
            List of unique case numbers (normalized)
        """
        # Normalize all case numbers and deduplicate
        raw_cases = df["Case Number"].unique().tolist()
        normalized = list(set(normalize_case_number(cn) for cn in raw_cases))
        return normalized

    def get_case_data(self, df: pd.DataFrame, case_number) -> Dict:
        """Get all data for a specific case.

        Args:
            df: Full DataFrame
            case_number: Case number to extract (will be normalized)

        Returns:
            Dictionary with case data
        """
        # Normalize the target case number
        target_normalized = normalize_case_number(case_number)

        # Filter for rows where normalized case number matches
        # This handles cases where Excel has "00090406" but we're looking for "90406"
        case_df = df[df["Case Number"].apply(normalize_case_number) == target_normalized].copy()

        if case_df.empty:
            return {}

        first_row = case_df.iloc[0]

        # Sort messages by date
        case_df_sorted = case_df.sort_values("Message Date")
        messages = case_df_sorted["Message"].tolist()
        dates = case_df_sorted["Message Date"].tolist()

        # Build full message text
        all_messages_text = "\n\n---MESSAGE---\n\n".join([
            f"[{dates[i].strftime('%b %d, %Y %I:%M %p') if isinstance(dates[i], pd.Timestamp) else 'Date Unknown'}] "
            f"Msg {i+1}: {str(msg)}"
            for i, msg in enumerate(messages)
            if pd.notna(msg)
        ])

        # Calculate engagement ratio
        interaction_count = len(case_df)
        engagement_ratio = 0.6 if interaction_count > 2 else 0.3

        return {
            "case_number": normalize_case_number(case_number),
            "customer_name": str(first_row["Customer Name"]),
            "severity": first_row["Severity"],
            "support_level": first_row["Support Level"],
            "created_date": (
                first_row["Created Date"].strftime("%Y-%m-%d")
                if isinstance(first_row["Created Date"], pd.Timestamp)
                else str(first_row["Created Date"])
            ),
            "last_modified_date": (
                first_row["Last Modified Date"].strftime("%Y-%m-%d")
                if isinstance(first_row["Last Modified Date"], pd.Timestamp)
                else str(first_row["Last Modified Date"])
            ),
            "status": str(first_row["Status"]),
            "case_age_days": int(first_row["case_age_days"]),
            "interaction_count": interaction_count,
            "customer_engagement_ratio": float(engagement_ratio),
            "messages_full": all_messages_text,
            "messages_list": messages,
            "message_dates": dates,
            "case_data": case_df,
        }

    def prepare_messages_for_analysis(self, case_data: Dict) -> str:
        """Prepare messages JSON for API analysis.

        Args:
            case_data: Case dictionary from get_case_data

        Returns:
            JSON string of messages
        """
        import json

        messages = case_data.get("messages_list", [])
        dates = case_data.get("message_dates", [])

        messages_to_analyze = []
        for i, msg in enumerate(messages):
            if pd.isna(msg):
                continue
            msg_str = str(msg).strip()
            if len(msg_str) > 2000:
                msg_str = msg_str[:2000] + "..."

            date_str = (
                dates[i].strftime('%b %d, %Y')
                if i < len(dates) and isinstance(dates[i], pd.Timestamp)
                else 'Unknown'
            )

            messages_to_analyze.append({
                'index': i + 1,
                'date': date_str,
                'text': msg_str
            })

        return json.dumps(messages_to_analyze, indent=2)

    def build_enhanced_message_history(self, case_data: pd.DataFrame) -> str:
        """
        Build message history with ownership attribution and delay information.

        Each message is marked with [CUSTOMER] or [SUPPORT] based on content heuristics,
        and includes delay attribution to identify response time issues.

        Args:
            case_data: DataFrame with case messages sorted by date

        Returns:
            String with enhanced message history including ownership tags
        """
        case_data_sorted = case_data.sort_values('Message Date')

        messages = []
        prev_date = None
        prev_is_customer = None

        for idx, row in case_data_sorted.iterrows():
            msg = row.get('Message', '')
            if pd.isna(msg):
                continue

            msg_date = row.get('Message Date')
            msg_str = str(msg).strip()

            # Determine if this is a customer or support message
            is_customer = self._detect_message_ownership(msg_str, prev_is_customer)

            # Calculate delay attribution
            delay_info = ""
            if prev_date is not None and msg_date is not None:
                try:
                    if isinstance(prev_date, pd.Timestamp) and isinstance(msg_date, pd.Timestamp):
                        days_diff = (msg_date - prev_date).days
                        if days_diff > 0:
                            if is_customer and not prev_is_customer:
                                delay_info = f" ({days_diff}d delay - CUSTOMER not responding)"
                            elif not is_customer and prev_is_customer:
                                delay_info = f" ({days_diff}d delay - SUPPORT responsible)"
                except:
                    pass

            ownership = "[CUSTOMER]" if is_customer else "[SUPPORT]"
            date_str = msg_date.strftime('%b %d, %Y') if isinstance(msg_date, pd.Timestamp) else 'Unknown'

            # Truncate very long messages
            msg_display = msg_str[:2000] if len(msg_str) > 2000 else msg_str

            messages.append(f"{ownership} [{date_str}]{delay_info}\n{msg_display}")

            prev_date = msg_date
            prev_is_customer = is_customer

        return "\n\n---\n\n".join(messages)

    def _detect_message_ownership(self, msg_str: str, prev_is_customer: bool = None) -> bool:
        """
        Detect whether a message is from customer or support based on content patterns.

        Args:
            msg_str: Message text
            prev_is_customer: Previous message ownership (for alternating fallback)

        Returns:
            True if customer message, False if support message
        """
        msg_lower = msg_str.lower()

        # Customer indicators
        customer_indicators = [
            '@' in msg_str and 'truenas' not in msg_lower and 'ixsystems' not in msg_lower,
            'thank you' in msg_lower and 'we thank' not in msg_lower,
            'please help' in msg_lower,
            'we are experiencing' in msg_lower,
            'our ' in msg_lower and ('system' in msg_lower or 'server' in msg_lower or 'storage' in msg_lower),
            'i am' in msg_lower and 'experiencing' in msg_lower,
            'can you' in msg_lower and 'help' in msg_lower,
        ]

        # Support indicators
        support_indicators = [
            'truenas' in msg_lower or 'ixsystems' in msg_lower,
            'i have reviewed' in msg_lower,
            'please let me know' in msg_lower,
            'i will' in msg_lower and ('follow up' in msg_lower or 'investigate' in msg_lower),
            'we will' in msg_lower and ('dispatch' in msg_lower or 'schedule' in msg_lower),
            'support team' in msg_lower,
            'case update' in msg_lower,
            'attached debug' in msg_lower or 'debug attached' in msg_lower,
        ]

        if any(customer_indicators):
            return True
        elif any(support_indicators):
            return False
        else:
            # Default to alternating if no clear indicators
            return not prev_is_customer if prev_is_customer is not None else True


def build_enhanced_message_history(case_data: pd.DataFrame) -> str:
    """
    Standalone function to build enhanced message history.
    Wrapper around DataLoader method for backward compatibility.

    Args:
        case_data: DataFrame with case messages

    Returns:
        Enhanced message history string
    """
    loader = DataLoader()
    return loader.build_enhanced_message_history(case_data)
