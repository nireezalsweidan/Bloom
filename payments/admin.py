# payments/admin.py
from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["order", "method", "status", "amount", "created_at"]
    list_filter = ["method", "status"]