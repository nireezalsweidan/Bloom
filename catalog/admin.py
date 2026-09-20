from django.contrib import admin
from .models import Category, Tag, Item


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "stock_quantity", "is_available"]
    list_filter = ["category", "tags", "is_available"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ["tags"]