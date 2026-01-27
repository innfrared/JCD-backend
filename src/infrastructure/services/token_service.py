"""JWT token service."""
from rest_framework_simplejwt.tokens import RefreshToken
from src.application.shared.auth import TokenPair


class TokenService:
    """JWT token service."""
    
    @staticmethod
    def generate_tokens(user_id: int, email: str, is_staff: bool) -> TokenPair:
        """Generate access and refresh tokens."""
        refresh = RefreshToken()
        refresh['user_id'] = user_id
        refresh['email'] = email
        refresh['is_staff'] = is_staff
        
        return TokenPair(
            access=str(refresh.access_token),
            refresh=str(refresh)
        )
    
    @staticmethod
    def refresh_token(refresh_token: str) -> TokenPair:
        """Refresh access token."""
        token = RefreshToken(refresh_token)
        return TokenPair(
            access=str(token.access_token),
            refresh=str(token)
        )

