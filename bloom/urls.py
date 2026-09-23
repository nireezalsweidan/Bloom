from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("shop/", include("catalog.urls")),
    path("bouquet/", include("bouquets.urls")),
    path("", views.home, name="home"),
    path("ai/", include("ai_recommendations.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)