from django.contrib import admin
from .models import Bouquet, BouquetItem


class BouquetItemInline(admin.TabularInline):
    model = BouquetItem
    extra = 0


@admin.register(Bouquet)
class BouquetAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "occasion", "style", "status", "source", "price"]
    list_filter = ["status", "source", "occasion"]
    inlines = [BouquetItemInline]