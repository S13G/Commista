from django.urls import path

from accounts.utils import GoogleSocialAuthView
from accounts import views

urlpatterns = [
    path('google/', GoogleSocialAuthView.as_view()),
    path('register/', views.RegisterView.as_view())
]
