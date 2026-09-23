from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from catalog.models import Item
from bouquets.models import Bouquet
from .models import Cart, CartItem
from decimal import Decimal
from orders.views import FREE_DELIVERY_THRESHOLD


def _get_or_create_cart(user):
    cart, created = Cart.objects.get_or_create(user=user)
    if not created and cart.status != Cart.Status.ACTIVE:
        cart.status = Cart.Status.ACTIVE
        cart.save()
    return cart

@login_required
def cart_detail(request):
    cart = _get_or_create_cart(request.user)
    cart_items = cart.cart_items.select_related("item", "item__category", "bouquet").order_by("added_at")
    remaining_for_free_delivery = max(Decimal("0.00"), FREE_DELIVERY_THRESHOLD - cart.total_price)
    return render(request, "cart/cart_detail.html", {
        "cart": cart,
        "cart_items": cart_items,
        "remaining_for_free_delivery": remaining_for_free_delivery,
    })

@login_required
def add_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, is_available=True)
    if request.method != "POST":
        return redirect("catalog:item_detail", slug=item.slug)

    qty = max(1, int(request.POST.get("quantity", 1) or 1))
    cart = _get_or_create_cart(request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, item=item, defaults={"quantity": qty, "unit_price": item.price}
    )
    if not created:
        cart_item.quantity += qty
        cart_item.save()

    messages.success(request, f"Added {item.name} to your cart.")
    return redirect("cart:cart_detail")


@login_required
def add_bouquet(request, bouquet_id):
    bouquet = get_object_or_404(Bouquet, id=bouquet_id, user=request.user)
    if request.method != "POST":
        return redirect("bouquets:bouquet_detail", pk=bouquet.pk)

    cart = _get_or_create_cart(request.user)
    existing = CartItem.objects.filter(cart=cart, bouquet=bouquet).first()
    if existing:
        existing.quantity += 1
        existing.save()
    else:
        CartItem.objects.create(cart=cart, bouquet=bouquet, quantity=1, unit_price=bouquet.price)

    messages.success(request, "Bouquet added to your cart.")
    return redirect("cart:cart_detail")


@login_required
def update_quantity(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "increase":
            cart_item.quantity += 1
            cart_item.save()
        elif action == "decrease":
            cart_item.quantity -= 1
            if cart_item.quantity <= 0:
                cart_item.delete()
            else:
                cart_item.save()
    return redirect("cart:cart_detail")


@login_required
def remove_item(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    if request.method == "POST":
        cart_item.delete()
        messages.info(request, "Item removed from cart.")
    return redirect("cart:cart_detail")