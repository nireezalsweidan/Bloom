from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from bouquets.models import Bouquet, BouquetItem
from catalog.models import Item
from .models import AIRecommendation
from .services import generate_recommendation, validate_recommendation, AIGenerationError

COLOR_PALETTE_CHOICES = [
    "Soft Pastels & Blush Rose", "Sunset Terracotta & Warm Peach",
    "Pure Ivory & Botanical Sage", "Vibrant Jewel & Plum Velour",
]
CARD_TONES = [
    ("Romantic & Poetic", "To another year of growing together in beauty and love."),
    ("Heartfelt & Warm", "Every petal holds gratitude for your light and presence."),
    ("Brief & Elegant", "With deepest affection, today and always."),
]


@login_required
def ai_designer(request):
    latest_id = request.session.get("latest_ai_recommendation_id")
    latest_recommendation = None
    if latest_id:
        latest_recommendation = AIRecommendation.objects.filter(pk=latest_id, user=request.user).first()

    if request.method == "POST" and request.POST.get("form_action") == "generate":
        occasion = request.POST.get("occasion", "").strip()
        style = request.POST.get("style", "").strip()
        color_palette = request.POST.get("color_palette", "").strip()
        card_message_pref = request.POST.get("card_tone_text", "").strip()
        budget_raw = request.POST.get("budget", "95").strip()

        try:
            budget = Decimal(budget_raw)
        except InvalidOperation:
            budget = Decimal("95")

        if not occasion or not style:
            messages.error(request, "Please choose an occasion and a style.")
            return redirect("ai_recommendations:designer")

        recommendation = AIRecommendation.objects.create(
            user=request.user, occasion=occasion, style=style, budget=budget,
            input_data={
                "occasion": occasion, "style": style, "budget": str(budget),
                "color_palette": color_palette, "card_tone": card_message_pref,
            },
            status=AIRecommendation.Status.GENERATED,
        )

        try:
            raw = generate_recommendation(occasion, style, budget, color_palette, card_message_pref)
            cleaned, warnings = validate_recommendation(raw, budget)
            recommendation.output_data = cleaned
            recommendation.save()
            for w in warnings:
                messages.warning(request, w)
        except AIGenerationError as exc:
            recommendation.status = AIRecommendation.Status.FAILED
            recommendation.error_message = str(exc)
            recommendation.save()
            messages.error(
                request,
                "Our AI designer couldn't generate a bouquet right now. "
                "You can try again, or use the manual Bouquet Studio instead."
            )
            return redirect("ai_recommendations:designer")

        request.session["latest_ai_recommendation_id"] = recommendation.pk
        return redirect("ai_recommendations:designer")

    history = request.user.ai_recommendations.all()[:8]

    return render(request, "ai_recommendations/designer.html", {
        "occasion_choices": Bouquet.Occasion.choices,
        "style_choices": Bouquet.Style.choices,
        "color_palette_choices": COLOR_PALETTE_CHOICES,
        "card_tones": CARD_TONES,
        "latest_recommendation": latest_recommendation,
        "history": history,
    })


@login_required
def accept_recommendation(request, pk):
    recommendation = get_object_or_404(
        AIRecommendation, pk=pk, user=request.user, status=AIRecommendation.Status.GENERATED
    )
    if request.method != "POST":
        return redirect("ai_recommendations:designer")

    if not recommendation.output_data or not recommendation.output_data.get("flowers"):
        messages.error(request, "This recommendation has no usable flowers to accept.")
        return redirect("ai_recommendations:designer")

    greeting_card = None
    card_id = recommendation.output_data.get("greeting_card_item_id")
    if card_id:
        greeting_card = Item.objects.filter(id=card_id, is_available=True).first()

    bouquet = Bouquet.objects.create(
        user=request.user,
        occasion=recommendation.occasion,
        style=recommendation.style,
        budget=recommendation.budget,
        greeting_card=greeting_card,
        card_message=recommendation.output_data.get("card_message", ""),
        status=Bouquet.Status.SAVED,
        source=Bouquet.Source.AI,
        ai_recommendation=recommendation,
    )
    for flower in recommendation.output_data["flowers"]:
        item = Item.objects.filter(id=flower["item_id"], is_available=True).first()
        if item:
            BouquetItem.objects.create(bouquet=bouquet, item=item, quantity=flower["quantity"], unit_price=item.price)
    bouquet.recalculate_price()
    bouquet.save()

    recommendation.status = AIRecommendation.Status.ACCEPTED
    recommendation.save()

    if request.session.get("latest_ai_recommendation_id") == recommendation.pk:
        del request.session["latest_ai_recommendation_id"]

    messages.success(request, "Recommendation accepted and saved to your bouquets!")
    return redirect("bouquets:bouquet_detail", pk=bouquet.pk)


@login_required
def reject_recommendation(request, pk):
    recommendation = get_object_or_404(
        AIRecommendation, pk=pk, user=request.user, status=AIRecommendation.Status.GENERATED
    )
    if request.method == "POST":
        recommendation.status = AIRecommendation.Status.REJECTED
        recommendation.save()
        messages.info(request, "Recommendation rejected.")
    if request.session.get("latest_ai_recommendation_id") == recommendation.pk:
        del request.session["latest_ai_recommendation_id"]
    return redirect("ai_recommendations:designer")