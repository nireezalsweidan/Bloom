from django.urls import path
from .views import SignUpView, BloomLoginView, logout_view

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", BloomLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
]