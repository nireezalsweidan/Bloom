from django.urls import path
from .views import ItemListView, ItemDetailView

app_name = "catalog"

urlpatterns = [
    path("", ItemListView.as_view(), name="item_list"),
    path("<slug:slug>/", ItemDetailView.as_view(), name="item_detail"),
]