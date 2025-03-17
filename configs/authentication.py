from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from configs.models import User

class CustomTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "token":
            return None

        token = parts[1]

        try:
            user = User.objects.get(token=token)
            if not user.is_active:
                raise AuthenticationFailed("User is inactive")
        except User.DoesNotExist:
            raise AuthenticationFailed("Invalid token")

        return (user, None)
