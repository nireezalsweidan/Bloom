from django.urls import path
from . import views

app_name = "bouquets"

urlpatterns = [
    path("design/", views.bouquet_designer, name="design_new"),
    path("design/<int:pk>/edit/", views.bouquet_designer, name="design_edit"),
    path("my-bouquets/", views.bouquet_list, name="bouquet_list"),
    path("my-bouquets/<int:pk>/", views.bouquet_detail, name="bouquet_detail"),
    path("my-bouquets/<int:pk>/delete/", views.bouquet_delete, name="bouquet_delete"),
    path("my-bouquets/<int:pk>/clone/", views.bouquet_clone, name="bouquet_clone"),
]