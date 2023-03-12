from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from rest_framework.authentication import BaseAuthentication


class CustomHeaderAuthentication(BaseAuthentication):
    def authenticate(self, request):
        User = get_user_model()
        token = request.META.get('HTTP_X_CUSTOM_TOKEN')
        if not token:
            return None

        try:
            user = User.objects.get(auth_token=token)
        except User.DoesNotExist:
            return None

        return user, None


# class EmailBackend(BaseBackend):
#     def authenticate(self, request, username=None, password=None, **kwargs):
#         User = get_user_model()
#         try:
#             user = User.objects.get(email=username)
#         except User.DoesNotExist:
#             return None
#         else:
#             if user.check_password(password):
#                 return user
#         return None
