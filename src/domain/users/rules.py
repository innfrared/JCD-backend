"""User domain rules."""
from src.domain.shared.exceptions import BusinessRuleViolation


def ensure_user_is_active(user):
    """Ensure user is active."""
    if not user.is_active:
        raise BusinessRuleViolation("User account is not active")


def ensure_user_owns_address(user_id: int, address_user_id: int):
    """Ensure user owns the address."""
    if user_id != address_user_id:
        raise BusinessRuleViolation("User does not own this address")

