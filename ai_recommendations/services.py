import json
import logging
from decimal import Decimal

from django.conf import settings

from catalog.models import Item

logger = logging.getLogger(__name__)


class AIGenerationError(Exception):
    """Raised on any provider failure, timeout, or malformed AI response."""


def _catalog_context(max_items=60):
    items = (
        Item.objects.filter(is_available=True, category__slug__in=["flowers", "greeting-cards"])
        .select_related("category")
        .prefetch_related("tags")[:max_items]
    )
    return [
        {
            "id": item.id, "name": item.name, "category": item.category.slug,
            "price": float(item.price), "tags": [t.name for t in item.tags.all()],
        }
        for item in items
    ]


def _build_prompt(occasion, style, budget, color_palette, card_tone):
    catalog = _catalog_context()
    return f"""You are Bloom's floral design assistant. Recommend a bouquet using ONLY the catalog items below (reference them by their exact "id"). Stay within the customer's budget where possible — do not exceed it by more than 10%.

Customer preferences:
- Occasion: {occasion}
- Style: {style}
- Budget: ${budget}
- Color palette: {color_palette}
- Card tone: {card_tone}

Catalog (JSON):
{json.dumps(catalog)}

Respond with ONLY valid JSON, no other text, matching exactly this shape:
{{
  "flowers": [{{"item_id": <int>, "quantity": <int>, "reason": "<short reason>"}}],
  "greeting_card_item_id": <int or null>,
  "card_message": "<a short personalized card message>",
  "style_reasoning": "<1-2 sentence explanation of the composition>"
}}"""


def _call_anthropic(prompt):
    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        raise AIGenerationError(f"AI provider request failed: {exc}") from exc
    return "".join(block.text for block in response.content if block.type == "text")


def _call_mock(occasion, style, budget, color_palette, card_tone):
    """
    Local rule-based fallback used when AI_PROVIDER=mock (no API key
    needed). Picks affordable flowers so the whole feature is testable
    end-to-end without external credentials.
    """
    catalog = _catalog_context()
    flowers_pool = sorted([c for c in catalog if c["category"] == "flowers"], key=lambda c: c["price"])
    cards_pool = [c for c in catalog if c["category"] == "greeting-cards"]

    selected = []
    total = Decimal("0")
    budget_dec = Decimal(str(budget))
    for item in flowers_pool:
        qty = 3
        cost = Decimal(str(item["price"])) * qty
        if total + cost > budget_dec * Decimal("1.1"):
            continue
        selected.append({"item_id": item["id"], "quantity": qty, "reason": f"A {style.lower()} accent within budget."})
        total += cost
        if len(selected) >= 3:
            break

    card = cards_pool[0] if cards_pool else None
    return json.dumps({
        "flowers": selected,
        "greeting_card_item_id": card["id"] if card else None,
        "card_message": f"Wishing you a wonderful {occasion.lower()}.",
        "style_reasoning": f"A {style.lower()} composition of seasonal stems chosen to fit your ${budget} budget.",
    })


def generate_recommendation(occasion, style, budget, color_palette, card_tone):
    """Returns a dict of raw AI output. Raises AIGenerationError on failure."""
    prompt = _build_prompt(occasion, style, budget, color_palette, card_tone)

    try:
        if settings.AI_PROVIDER == "anthropic":
            raw_text = _call_anthropic(prompt)
        else:
            raw_text = _call_mock(occasion, style, budget, color_palette, card_tone)
    except AIGenerationError:
        raise
    except Exception as exc:
        raise AIGenerationError(f"Unexpected AI provider error: {exc}") from exc

    try:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        return json.loads(cleaned)
    except (json.JSONDecodeError, IndexError) as exc:
        raise AIGenerationError(f"AI returned malformed JSON: {exc}") from exc


def validate_recommendation(data, budget):
    """
    Validates AI output against the real catalog. Returns (cleaned_data,
    warnings) or raises AIGenerationError if nothing usable survives.
    """
    if not isinstance(data, dict) or "flowers" not in data:
        raise AIGenerationError("AI response missing required 'flowers' field.")

    warnings = []
    valid_flowers = []
    total = Decimal("0")

    flower_ids = [f.get("item_id") for f in data.get("flowers", []) if isinstance(f, dict)]
    real_items = {item.id: item for item in Item.objects.filter(id__in=flower_ids, is_available=True)}

    for entry in data.get("flowers", []):
        item_id = entry.get("item_id")
        qty = entry.get("quantity")
        item = real_items.get(item_id)
        if item is None:
            warnings.append(f"AI recommended an item (id={item_id}) that doesn't exist or is unavailable — skipped.")
            continue
        if not isinstance(qty, int) or qty <= 0:
            warnings.append(f"AI gave an invalid quantity for {item.name} — skipped.")
            continue
        valid_flowers.append({
            "item_id": item.id, "name": item.name, "quantity": qty,
            "unit_price": float(item.price), "reason": entry.get("reason", ""),
        })
        total += item.price * qty

    if not valid_flowers:
        raise AIGenerationError("AI response contained no valid, in-catalog flowers.")

    card_item = None
    card_id = data.get("greeting_card_item_id")
    if card_id:
        card_item = Item.objects.filter(id=card_id, is_available=True, category__slug="greeting-cards").first()
        if card_item is None:
            warnings.append("AI recommended a greeting card that doesn't exist — skipped.")
        else:
            total += card_item.price

    if budget and total > Decimal(str(budget)) * Decimal("1.15"):
        warnings.append(f"This recommendation (${total}) is notably over your ${budget} budget.")

    return {
        "flowers": valid_flowers,
        "greeting_card_item_id": card_item.id if card_item else None,
        "greeting_card_name": card_item.name if card_item else None,
        "card_message": str(data.get("card_message", ""))[:300],
        "style_reasoning": str(data.get("style_reasoning", ""))[:600],
        "total_price": float(total),
    }, warnings