from django.urls import path
from . import views

app_name = "ai_recommendations"

urlpatterns = [
    path("", views.ai_designer, name="designer"),
    path("<int:pk>/accept/", views.accept_recommendation, name="accept"),
    path("<int:pk>/reject/", views.reject_recommendation, name="reject"),
]