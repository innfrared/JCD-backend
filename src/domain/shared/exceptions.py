"""Domain exceptions."""


class DomainException(Exception):
    """Base domain exception."""
    pass


class ValidationError(DomainException):
    """Validation error."""
    pass


class NotFoundError(DomainException):
    """Entity not found error."""
    pass


class BusinessRuleViolation(DomainException):
    """Business rule violation."""
    pass

