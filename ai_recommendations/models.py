from django.conf import settings
from django.db import models


class AIRecommendation(models.Model):
    class Status(models.TextChoices):
        GENERATED = "generated", "Generated"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_recommendations")

    occasion = models.CharField(max_length=20)
    style = models.CharField(max_length=20)
    budget = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    input_data = models.JSONField()
    output_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.GENERATED)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"AI Recommendation #{self.pk} ({self.status}) for {self.user}"