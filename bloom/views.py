from django.db.models import Count, Q
from django.shortcuts import render

from catalog.models import Category, Item

CATEGORY_META = {
    "flowers": {"icon": "spa", "cta": "Browse stems"},
    "bouquets": {"icon": "local_florist", "cta": "Shop ready-to-ship"},
    "greeting-cards": {"icon": "mail", "cta": "Discover paper goods"},
    "gifts": {"icon": "redeem", "cta": "View gifts"},
}


def home(request):
    categories = list(
        Category.objects.annotate(
            item_count=Count("items", filter=Q(items__is_available=True))
        )[:4]
    )
    for cat in categories:
        meta = CATEGORY_META.get(cat.slug, {"icon": "local_florist", "cta": "Browse"})
        cat.icon = meta["icon"]
        cat.cta_label = meta["cta"]

    featured_items = list(
        Item.objects.filter(category__slug="bouquets", is_available=True)
        .order_by("-created_at")[:4]
    )
    hero_item = featured_items[0] if featured_items else None

    return render(request, "home.html", {
        "categories": categories,
        "featured_items": featured_items,
        "hero_item": hero_item,
    })