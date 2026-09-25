from django.db import models
from orders.models import Order


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Cash on Delivery"
        CARD = "card", "Credit Card"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    method = models.CharField(max_length=10, choices=Method.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    card_last4 = models.CharField(max_length=4, blank=True)
    cardholder_name = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.order.order_number} ({self.method})"