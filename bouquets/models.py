from decimal import Decimal
from django.conf import settings
from django.db import models

from catalog.models import Item


class Bouquet(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SAVED = "saved", "Saved"
        ORDERED = "ordered", "Ordered"

    class Source(models.TextChoices):
        CUSTOM = "custom", "Custom"
        AI = "ai", "AI"

    class Occasion(models.TextChoices):
        BIRTHDAY = "birthday", "Birthday"
        ANNIVERSARY = "anniversary", "Anniversary"
        ROMANTIC = "romantic", "Romantic Gesture"
        SYMPATHY = "sympathy", "Sympathy"
        CELEBRATION = "celebration", "Celebration"
        THANK_YOU = "thank_you", "Thank You"

    class Style(models.TextChoices):
        ROMANTIC = "romantic", "Romantic"
        ELEGANT = "elegant", "Elegant"
        MODERN = "modern", "Modern & Minimal"
        RUSTIC = "rustic", "Rustic"
        CHEERFUL = "cheerful", "Cheerful & Bright"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bouquets")
    occasion = models.CharField(max_length=20, choices=Occasion.choices)
    style = models.CharField(max_length=20, choices=Style.choices)
    budget = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    greeting_card = models.ForeignKey(
        Item, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+", limit_choices_to={"category__slug": "greeting-cards"},
    )
    card_message = models.TextField(blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.CUSTOM)
    ai_recommendation = models.OneToOneField(
        "ai_recommendations.AIRecommendation",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="accepted_as_bouquet",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def recalculate_price(self):
        total = sum((bi.unit_price * bi.quantity for bi in self.items.all()), Decimal("0.00"))
        if self.greeting_card:
            total += self.greeting_card.price
        self.price = total
        return total

    @property
    def total_stems(self):
        return sum(bi.quantity for bi in self.items.all())

    def __str__(self):
        return f"Bouquet #{self.pk} ({self.get_occasion_display()}) — {self.user}"


class BouquetItem(models.Model):
    bouquet = models.ForeignKey(Bouquet, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="bouquet_items")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)  # price snapshot, per ERD note 7

    class Meta:
        unique_together = ("bouquet", "item")

    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.item.name}"
