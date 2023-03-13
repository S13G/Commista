from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication


class IsAuthenticatedJWT(BasePermission):
    """
    Custom permission class to check if user is authenticated with JWT token
    """

    def has_permission(self, request, view):
        auth = JWTAuthentication()
        user, auth_token = auth.authenticate(request)
        return bool(user and user.is_authenticated)
