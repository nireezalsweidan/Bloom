from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from catalog.models import Item
from .models import Bouquet, BouquetItem

from django.db.models import Sum

@login_required
def bouquet_designer(request, pk=None):
    bouquet = None
    if pk:
        bouquet = get_object_or_404(Bouquet, pk=pk, user=request.user, status=Bouquet.Status.DRAFT)

    flowers = Item.objects.filter(category__slug="flowers", is_available=True)
    cards = Item.objects.filter(category__slug="greeting-cards", is_available=True)

    # defaults for GET (new or prefilled from an existing draft)
    existing_qty = {bi.item_id: bi.quantity for bi in bouquet.items.all()} if bouquet else {}
    selected_card_id = bouquet.greeting_card_id if bouquet else None
    card_message = bouquet.card_message if bouquet else ""
    selected_occasion = bouquet.occasion if bouquet else ""
    selected_style = bouquet.style if bouquet else ""
    selected_budget = bouquet.budget if bouquet else ""

    if request.method == "POST":
        occasion = request.POST.get("occasion", "")
        style = request.POST.get("style", "")
        budget_raw = request.POST.get("budget", "").strip()
        action = request.POST.get("action")  # "draft" or "save"
        greeting_card_id = request.POST.get("greeting_card_id") or None
        card_message_input = request.POST.get("card_message", "").strip()

        try:
            budget = Decimal(budget_raw) if budget_raw else None
        except InvalidOperation:
            budget = None

        selected_items = {}
        for item in flowers:
            qty_raw = request.POST.get(f"qty_{item.id}", "0").strip()
            qty = int(qty_raw) if qty_raw.isdigit() else 0
            if qty > 0:
                selected_items[item.id] = qty

        errors = []
        if not occasion or not style:
            errors.append("Please choose an occasion and a style.")
        if not selected_items:
            errors.append("Select at least one flower and quantity.")

        if errors:
            for e in errors:
                messages.error(request, e)
            # keep what the user entered so the page re-renders with it
            existing_qty = selected_items
            selected_card_id = int(greeting_card_id) if greeting_card_id else None
            card_message = card_message_input
            selected_occasion = occasion
            selected_style = style
            selected_budget = budget_raw
        else:
            status = Bouquet.Status.SAVED if action == "save" else Bouquet.Status.DRAFT
            greeting_card = Item.objects.filter(id=greeting_card_id).first() if greeting_card_id else None

            if bouquet:
                bouquet.occasion = occasion
                bouquet.style = style
                bouquet.budget = budget
                bouquet.greeting_card = greeting_card
                bouquet.card_message = card_message_input
                bouquet.status = status
                bouquet.save()
                bouquet.items.all().delete()
            else:
                bouquet = Bouquet.objects.create(
                    user=request.user, occasion=occasion, style=style, budget=budget,
                    greeting_card=greeting_card, card_message=card_message_input,
                    status=status, source=Bouquet.Source.CUSTOM,
                )

            for item_id, qty in selected_items.items():
                item = Item.objects.get(id=item_id)
                BouquetItem.objects.create(bouquet=bouquet, item=item, quantity=qty, unit_price=item.price)

            bouquet.recalculate_price()
            bouquet.save()

            messages.success(request, "Your bouquet has been saved!")
            return redirect("bouquets:bouquet_list")

    flowers_with_qty = [
        {"item": item, "quantity": existing_qty.get(item.id, 0)} for item in flowers
    ]

    return render(request, "bouquets/design.html", {
        "bouquet": bouquet,
        "flowers_with_qty": flowers_with_qty,
        "cards": cards,
        "selected_card_id": selected_card_id,
        "card_message": card_message,
        "selected_occasion": selected_occasion,
        "selected_style": selected_style,
        "selected_budget": selected_budget,
        "occasion_choices": Bouquet.Occasion.choices,
        "style_choices": Bouquet.Style.choices,
    })


@login_required
def bouquet_list(request):
    bouquets = request.user.bouquets.all().order_by("-updated_at")
    return render(request, "bouquets/bouquet_list.html", {"bouquets": bouquets})


@login_required
def bouquet_detail(request, pk):
    bouquet = get_object_or_404(Bouquet, pk=pk, user=request.user)
    return render(request, "bouquets/bouquet_detail.html", {"bouquet": bouquet})


@login_required
def bouquet_delete(request, pk):
    bouquet = get_object_or_404(Bouquet, pk=pk, user=request.user)
    if request.method == "POST":
        bouquet.delete()
        messages.success(request, "Bouquet deleted.")
    return redirect("bouquets:bouquet_list")

@login_required
def bouquet_list(request):
    sort = request.GET.get("sort", "recent")
    bouquets = request.user.bouquets.all().prefetch_related("items__item", "greeting_card")

    if sort == "price_asc":
        bouquets = bouquets.order_by("price")
    elif sort == "price_desc":
        bouquets = bouquets.order_by("-price")
    elif sort == "stems":
        bouquets = bouquets.annotate(stem_total=Sum("items__quantity")).order_by("-stem_total")
    else:
        bouquets = bouquets.order_by("-updated_at")

    counts = {
        "all": request.user.bouquets.count(),
        "saved": request.user.bouquets.filter(status=Bouquet.Status.SAVED).count(),
        "drafts": request.user.bouquets.filter(status=Bouquet.Status.DRAFT).count(),
        "ordered": request.user.bouquets.filter(status=Bouquet.Status.ORDERED).count(),
        "ai": request.user.bouquets.filter(source=Bouquet.Source.AI).count(),
    }

    return render(request, "bouquets/bouquet_list.html", {
        "bouquets": bouquets, "counts": counts, "sort": sort,
    })


@login_required
def bouquet_clone(request, pk):
    original = get_object_or_404(Bouquet, pk=pk, user=request.user)
    if request.method == "POST":
        clone = Bouquet.objects.create(
            user=request.user,
            occasion=original.occasion,
            style=original.style,
            budget=original.budget,
            greeting_card=original.greeting_card,
            card_message=original.card_message,
            status=Bouquet.Status.DRAFT,
            source=Bouquet.Source.CUSTOM,
        )
        for bi in original.items.all():
            BouquetItem.objects.create(bouquet=clone, item=bi.item, quantity=bi.quantity, unit_price=bi.item.price)
        clone.recalculate_price()
        clone.save()
        messages.success(request, "Bouquet cloned as a new draft.")
        return redirect("bouquets:design_edit", pk=clone.pk)
    return redirect("bouquets:bouquet_list")