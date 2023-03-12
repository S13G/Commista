from django.urls import path

from accounts import views
from accounts.utils import GoogleSocialAuthView

urlpatterns = [
    path('google/', GoogleSocialAuthView.as_view()),
    path('register/', views.RegisterView.as_view()),
    path('verify-email/', views.VerifyEmailView.as_view()),
    path('login/', views.LoginView.as_view()),
]
