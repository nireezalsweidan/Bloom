import random
import string

from django.conf import settings
from django.db import models

from catalog.models import Item
from bouquets.models import Bouquet


def generate_order_number():
    return "BL-" + "".join(random.choices(string.digits, k=6))


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    order_number = models.CharField(max_length=20, unique=True, default=generate_order_number)
    date = models.DateTimeField(auto_now_add=True)

    recipient_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    delivery_address = models.CharField(max_length=255)
    apartment = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    delivery_instructions = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=9, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=9, decimal_places=2)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    bouquet = models.ForeignKey(Bouquet, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    name_snapshot = models.CharField(max_length=200)  # preserved even if item/bouquet is later deleted
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.name_snapshot}"