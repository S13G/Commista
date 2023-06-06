from rest_framework import throttling


class AuthenticatedScopeRateThrottle(throttling.ScopedRateThrottle):
    def allow_request(self, request, view):
        if not request.user.is_authenticated:
            return False  # Disallow unauthenticated users to bypass throttling
        return super().allow_request(request, view)
