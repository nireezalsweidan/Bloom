from django.contrib import admin
from .models import AIRecommendation


@admin.register(AIRecommendation)
class AIRecommendationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "occasion", "style", "budget", "status", "created_at"]
    list_filter = ["status", "occasion"]
    readonly_fields = ["input_data", "output_data", "error_message", "created_at", "updated_at"]