from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_detail, name="cart_detail"),
    path("add/item/<int:item_id>/", views.add_item, name="add_item"),
    path("add/bouquet/<int:bouquet_id>/", views.add_bouquet, name="add_bouquet"),
    path("update/<int:pk>/", views.update_quantity, name="update_quantity"),
    path("remove/<int:pk>/", views.remove_item, name="remove_item"),
]