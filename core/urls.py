from django.urls import path

from core import views
from core.utils import GoogleSocialAuthView

urlpatterns = [
    path('change-email/', views.ChangeEmailView.as_view(), name="change_email"),
    path('change-password/', views.ChangePasswordView.as_view(), name="change_password"),
    path('google/', GoogleSocialAuthView.as_view(), name="google_auth"),
    path('login/', views.LoginView.as_view(), name="login"),
    path('logout/', views.LogoutView.as_view(), name="logout"),
    path('refresh-token/', views.RefreshView.as_view(), name="refresh_token"),
    path('register/', views.RegisterView.as_view(), name="register"),
    path('request-email-change-code/', views.RequestEmailChangeCodeView.as_view(), name="request_email_change_code"),
    path('request-password-reset-code/', views.RequestNewPasswordCodeView.as_view(), name="request_password_code"),
    path('resend-verification-code/', views.ResendEmailVerificationView.as_view(), name="resend_verification_code"),
    path('verify-email/', views.VerifyEmailView.as_view(), name="verify_email"),
]
