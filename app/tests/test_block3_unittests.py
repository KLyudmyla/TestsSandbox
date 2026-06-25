import datetime
import pytest
from datetime import datetime, timedelta


# =====================================================================
# Custom Exceptions for Corporate Business Logic
# =====================================================================

class SubscriptionExpiredError(Exception):
    """Raised when an operation is attempted on an expired subscription."""
    pass

# =====================================================================
# BLOCK 3: Date, Time & Expiration Logic
# ---------------------------------------------------------------------
# Testing Guidance:
# - CRITICAL: Do NOT use dynamic time like 'datetime.now()' in tests.
# - Inject hardcoded 'current_time' values to make assertions entirely deterministic.
# - Test critical threshold transitions: exactly active, exactly inside grace period, and fully expired.
# =====================================================================

class SubscriptionManager:
    """
    Handles user subscription statuses, expiration alerts, and grace periods.
    """

    def __init__(self, user_id: str, plan_type: str, expires_at: datetime):
        """
        Initializes the manager for a specific user subscription.
        """
        self.user_id = user_id
        self.plan_type = plan_type
        self.expires_at = expires_at

    def verify_access(self, current_time: datetime) -> str:
        """
        Verifies if the user has access to the platform based on current time.

        :param current_time: Naive datetime object representing the point of evaluation.
        :return: A string status ('active' or 'grace_period').
        :raises SubscriptionExpiredError: If the subscription is fully expired (past the 3-day grace period).
        """
        if current_time < self.expires_at:
            return "active"

        grace_end = self.expires_at + timedelta(days=3)
        if self.expires_at <= current_time <= grace_end:
            return "grace_period"

        raise SubscriptionExpiredError(f"Access denied. User subscription expired on {self.expires_at}.")


class TestSubscriptionManager:

    def test_verifying_access_with_active_subscription(self):
        output = SubscriptionManager("user1", "plan1", datetime(2027, 1, 1))
        current_time = datetime(2026, 6, 19, 16, 00, 00)
        assert output.verify_access(current_time) == "active"

    def test_verifying_access_within_grace_period(self):
        output = SubscriptionManager("user1", "plan1", datetime(2026, 6, 16))
        current_time = datetime(2026, 6, 18, 16, 00, 00)
        assert output.verify_access(current_time) == "grace_period"

    def test_raising_error_on_expired_subscription(self):
        output = SubscriptionManager("user1", "plan1", datetime(2020, 1, 1))
        current_time = datetime(2026, 6, 19, 16, 00, 00)
        with pytest.raises(SubscriptionExpiredError, match="Access denied. User subscription expired on 2020-01-01 00:00:00."):
            output.verify_access(current_time)
