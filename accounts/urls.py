from django.urls import path

from accounts import views
from accounts.utils import GoogleSocialAuthView

urlpatterns = [
    path('change-email/', views.ChangeEmailView.as_view()),
    path('change-password/', views.ChangePasswordView.as_view()),
    path('google/', GoogleSocialAuthView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('refresh-token/', views.RefreshView.as_view()),
    path('register/', views.RegisterView.as_view()),
    path('request-email-change-code/', views.RequestEmailChangeCodeView.as_view()),
    path('request-password-reset-code/', views.RequestNewPasswordCodeView.as_view()),
    path('resend-verification-code/', views.ResendEmailVerificationView.as_view()),
    path('verify-email/', views.VerifyEmailView.as_view()),
]
