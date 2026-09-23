from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from catalog.models import Item
from bouquets.models import Bouquet


class Cart(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ORDERED = "ordered", "Ordered"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_price(self):
        return sum((ci.subtotal for ci in self.cart_items.all()), Decimal("0.00"))

    @property
    def total_quantity(self):
        return sum(ci.quantity for ci in self.cart_items.all())

    def __str__(self):
        return f"Cart for {self.user}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, blank=True, related_name="cart_items")
    bouquet = models.ForeignKey(Bouquet, on_delete=models.CASCADE, null=True, blank=True, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)  # price snapshot — STORY-19
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(item__isnull=False, bouquet__isnull=True) |
                    models.Q(item__isnull=True, bouquet__isnull=False)
                ),
                name="cart_item_exactly_one_of_item_or_bouquet",
            )
        ]

    def clean(self):
        if bool(self.item_id) == bool(self.bouquet_id):
            raise ValidationError("A cart item must reference exactly one of item or bouquet.")

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    @property
    def name(self):
        return self.item.name if self.item else f"{self.bouquet.get_occasion_display()} Bouquet"

    def __str__(self):
        return f"{self.quantity} x {self.name}"