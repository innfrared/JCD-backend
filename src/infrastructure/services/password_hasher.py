"""Password hashing service."""
from django.contrib.auth.hashers import make_password, check_password


class PasswordHasher:
    """Password hashing service."""
    
    @staticmethod
    def hash(password: str) -> str:
        """Hash a password."""
        return make_password(password)
    
    @staticmethod
    def verify(password: str, password_hash: str) -> bool:
        """Verify a password against a hash."""
        return check_password(password, password_hash)

