import re
from typing import List
import pytest


# =====================================================================
# Custom Exceptions for Corporate Business Logic
# =====================================================================

class ValidationError(Exception):
    """Raised when user input fails validation rules."""
    pass

class InvalidLogFormatException(Exception):
    """Raised when a log line does not match the expected server format."""
    pass

# =====================================================================
# BLOCK 2: Text Parsing & Log Analysis
# ---------------------------------------------------------------------
# Testing Guidance:
# - Test structural integrity by supplying corrupted log strings.
# - Verify error handling behavior using 'pytest.raises' for empty arrays and ValueError conditions.
# - Ensure regular expressions are tested against multiple edge cases (e.g., adjacent error codes).
# =====================================================================

class LogParser:
    """
    A utility class to parse server logs and extract severity levels and HTTP error codes.
    """

    def __init__(self, raw_logs: List[str]):
        """
        Initializes the parser with a list of raw log lines.
        """
        self.logs = raw_logs

    def get_logs_by_level(self, level: str) -> List[str]:
        """
        Filters logs by severity level (e.g., 'INFO', 'WARNING', 'ERROR').
        Expects strict log format: 'YYYY-MM-DD HH:MM:SS [LEVEL] Message text'

        :param level: The severity level string to filter by.
        :return: A list of log lines that match the given severity level.
        :raises InvalidLogFormatException: If any log line doesn't match the required structure.
        """
        upper_level = level.upper()
        pattern = f"\\[{upper_level}\\]"

        filtered_logs = []
        for line in self.logs:
            if not re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[.*?\]", line):
                raise InvalidLogFormatException(f"Log line structure is corrupted: '{line}'")

            if re.search(pattern, line):
                filtered_logs.append(line)

        return filtered_logs

    def extract_error_codes(self) -> List[int]:
        """
        Finds and extracts all HTTP error status codes (4xx and 5xx) inside log messages.

        :return: A list of integers representing the extracted HTTP error codes.
        :raises ValueError: If the logs list is empty.
        """
        if not self.logs:
            raise ValueError("Cannot extract error codes from an empty log history.")

        error_codes = []
        for line in self.logs:
            matches = re.findall(r'\b[45]\d{2}\b', line)
            for match in matches:
                error_codes.append(int(match))
        return error_codes

# I have to create a fixture in order not to repeat test data in each function
@pytest.fixture
def my_logs():
    return [
        "2026-06-10 10:00:00 [INFO] Server started successfully",
        "2026-06-18 10:05:00 [WARNING] User is not authorized: 401",
        "2026-06-18 10:10:00 [ERROR] Database connection failed",
        "2026-06-19 10:05:08 [WARNING] Bad Request: 400",
        "2026-06-19 10:11:22 [WARNING] Too Many Requests: 429",
        "2026-06-19 10:15:08 [ERROR] Internal Server Error: 500",
        "2026-06-19 11:15:08 [ERROR] Gateway Timeout: 504",
    ]

@pytest.fixture
def broken_logs():
    return [
        "2026-06-1 10:00:000 [INFO] Server started successfully",
        "2026-06-18 10:05:00 [WARNING]",
        "2026-06-18 10:10:00 [ERROR] Database connection failed"
    ]

class TestLogParser:

    def test_get_error_logs(self, my_logs): # positive scenario, logs are found
        res = LogParser(my_logs)
        actual = res.get_logs_by_level("ERROR")
        print(actual)
        expected = [
            "2026-06-18 10:10:00 [ERROR] Database connection failed",
            "2026-06-19 10:15:08 [ERROR] Internal Server Error: 500",
            "2026-06-19 11:15:08 [ERROR] Gateway Timeout: 504",]
        assert actual == expected

    def test_raising_exception_for_logs(self, broken_logs): # raising exception with incorrect date format
        res = LogParser(broken_logs)
        with pytest.raises(InvalidLogFormatException, match=f"Log line structure is corrupted: "):
            res.get_logs_by_level("ERROR")

    def test_raising_exception_for_warning(self, broken_logs): # raising exception with regular expression format
        res = LogParser(broken_logs)
        with pytest.raises(InvalidLogFormatException, match=f"Log line structure is corrupted: "):
            res.get_logs_by_level("WARNING")

    def test_empty_list_for_logs(self): # verifying empty list with errors
        res = LogParser([])
        assert res.get_logs_by_level("DEBUG") == []

    def test_appending_function_for_logs(self, my_logs): # verifying that lines are appended
        res = LogParser(my_logs)
        actual = res.get_logs_by_level("WARNING")
        assert len(actual) == 3

    def test_return_all_codes(self, my_logs):
        res = LogParser(my_logs)
        expected = [401, 400, 429, 500, 504]
        assert res.extract_error_codes() == expected

    def test_return_validation_error_for_empty_logs(self):
        res = LogParser([])
        with pytest.raises(ValueError, match="Cannot extract error codes from an empty log history."):
            res.extract_error_codes()
