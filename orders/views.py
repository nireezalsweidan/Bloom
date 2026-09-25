from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from cart.models import Cart, CartItem
from payments.models import Payment
from .models import Order, OrderItem
from django.db.models import Q
from bouquets.models import Bouquet, BouquetItem
import re
from datetime import date

DELIVERY_FEE = Decimal("12.00")
FREE_DELIVERY_THRESHOLD = Decimal("75.00")


@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user, status=Cart.Status.ACTIVE).first()
    cart_items = cart.cart_items.select_related("item", "bouquet") if cart else []

    if not cart_items:
        messages.warning(request, "Your cart is empty.")
        return redirect("cart:cart_detail")

    subtotal = sum((ci.subtotal for ci in cart_items), Decimal("0.00"))
    delivery_fee = Decimal("0.00") if subtotal >= FREE_DELIVERY_THRESHOLD else DELIVERY_FEE
    total = subtotal + delivery_fee

    if request.method == "POST":
        recipient_name = request.POST.get("recipient_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        apartment = request.POST.get("apartment", "").strip()
        city = request.POST.get("city", "").strip()
        postal_code = request.POST.get("postal_code", "").strip()
        instructions = request.POST.get("instructions", "").strip()
        payment_method = request.POST.get("payment_method", "cash")

        if not all([recipient_name, phone, address, city, postal_code]):
            messages.error(request, "Please fill in all required delivery fields.")
            return render(request, "orders/checkout.html", {
                "cart_items": cart_items, "subtotal": subtotal,
                "delivery_fee": delivery_fee, "total": total,
            })

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                recipient_name=recipient_name, phone=phone,
                delivery_address=address, apartment=apartment,
                city=city, postal_code=postal_code,
                delivery_instructions=instructions,
                subtotal=subtotal, delivery_fee=delivery_fee, total_price=total,
                status=Order.Status.CONFIRMED,
            )
            for ci in cart_items:
                OrderItem.objects.create(
                    order=order, item=ci.item, bouquet=ci.bouquet,
                    name_snapshot=ci.name, quantity=ci.quantity, unit_price=ci.unit_price,
                )
                if ci.bouquet:
                    ci.bouquet.status = ci.bouquet.Status.ORDERED
                    ci.bouquet.save()

            Payment.objects.create(
                order=order, method=payment_method, amount=total,
                status=Payment.Status.PENDING if payment_method == "cash" else Payment.Status.PAID,
            )

            cart.status = Cart.Status.ORDERED
            cart.save()
            CartItem.objects.filter(cart=cart).delete()

        return redirect("orders:order_confirmation", order_number=order.order_number)

    return render(request, "orders/checkout.html", {
        "cart_items": cart_items, "subtotal": subtotal,
        "delivery_fee": delivery_fee, "total": total,
    })


@login_required
def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, "orders/order_confirmation.html", {"order": order})


@login_required
def order_list(request):
    status_filter = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()

    orders = request.user.orders.all().prefetch_related("items", "payment")
    if status_filter:
        orders = orders.filter(status=status_filter)
    if query:
        orders = orders.filter(Q(order_number__icontains=query) | Q(recipient_name__icontains=query))

    counts = {
        "all": request.user.orders.count(),
        "pending": request.user.orders.filter(status=Order.Status.PENDING).count(),
        "confirmed": request.user.orders.filter(status=Order.Status.CONFIRMED).count(),
        "delivered": request.user.orders.filter(status=Order.Status.DELIVERED).count(),
        "cancelled": request.user.orders.filter(status=Order.Status.CANCELLED).count(),
    }

    return render(request, "orders/order_list.html", {
        "orders": orders, "counts": counts, "status_filter": status_filter, "query": query,
    })

@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, "orders/order_detail.html", {"order": order})


@login_required
def reorder(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if request.method != "POST":
        return redirect("orders:order_detail", order_number=order.order_number)

    cart, _ = Cart.objects.get_or_create(user=request.user)
    if cart.status != Cart.Status.ACTIVE:
        cart.status = Cart.Status.ACTIVE
        cart.save()

    added, skipped = 0, 0
    for oi in order.items.all():
        if oi.item and oi.item.is_available:
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, item=oi.item, defaults={"quantity": oi.quantity, "unit_price": oi.item.price}
            )
            if not created:
                cart_item.quantity += oi.quantity
                cart_item.save()
            added += 1
        elif oi.bouquet:
            clone = Bouquet.objects.create(
                user=request.user, occasion=oi.bouquet.occasion, style=oi.bouquet.style,
                budget=oi.bouquet.budget, greeting_card=oi.bouquet.greeting_card,
                card_message=oi.bouquet.card_message, status=Bouquet.Status.SAVED,
                source=oi.bouquet.source,
            )
            for bi in oi.bouquet.items.all():
                BouquetItem.objects.create(bouquet=clone, item=bi.item, quantity=bi.quantity, unit_price=bi.item.price)
            clone.recalculate_price()
            clone.save()
            CartItem.objects.create(cart=cart, bouquet=clone, quantity=oi.quantity, unit_price=clone.price)
            added += 1
        else:
            skipped += 1

    if added:
        messages.success(request, f"Added {added} item(s) back to your cart.")
    if skipped:
        messages.warning(request, f"{skipped} item(s) from this order are no longer available and were skipped.")
    return redirect("cart:cart_detail")

@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user, status=Cart.Status.ACTIVE).first()
    cart_items = cart.cart_items.select_related("item", "bouquet") if cart else []

    if not cart_items:
        messages.warning(request, "Your cart is empty.")
        return redirect("cart:cart_detail")

    subtotal = sum((ci.subtotal for ci in cart_items), Decimal("0.00"))
    delivery_fee = Decimal("0.00") if subtotal >= FREE_DELIVERY_THRESHOLD else DELIVERY_FEE
    total = subtotal + delivery_fee
    context = {"cart_items": cart_items, "subtotal": subtotal, "delivery_fee": delivery_fee, "total": total}

    if request.method == "POST":
        recipient_name = request.POST.get("recipient_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        apartment = request.POST.get("apartment", "").strip()
        city = request.POST.get("city", "").strip()
        postal_code = request.POST.get("postal_code", "").strip()
        instructions = request.POST.get("instructions", "").strip()
        payment_method = request.POST.get("payment_method", "cash")

        errors = []
        if not all([recipient_name, phone, address, city, postal_code]):
            errors.append("Please fill in all required delivery fields.")

        card_last4 = ""
        cardholder_name = ""

        if payment_method == "card":
            card_number = re.sub(r"\s+", "", request.POST.get("card_number", ""))
            expiry = request.POST.get("card_expiry", "").strip()
            cvc = request.POST.get("card_cvc", "").strip()
            cardholder_name = request.POST.get("card_name", "").strip()

            if not (card_number.isdigit() and 13 <= len(card_number) <= 19):
                errors.append("Please enter a valid card number.")
            else:
                card_last4 = card_number[-4:]

            if not re.match(r"^(0[1-9]|1[0-2])/\d{2}$", expiry):
                errors.append("Expiration date must be in MM/YY format.")
            else:
                exp_month, exp_year = expiry.split("/")
                today = date.today()
                if (2000 + int(exp_year), int(exp_month)) < (today.year, today.month):
                    errors.append("This card has expired.")

            if not (cvc.isdigit() and 3 <= len(cvc) <= 4):
                errors.append("Please enter a valid security code (CVC).")
            if not cardholder_name:
                errors.append("Please enter the name on the card.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, "orders/checkout.html", context)

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user, recipient_name=recipient_name, phone=phone,
                delivery_address=address, apartment=apartment, city=city, postal_code=postal_code,
                delivery_instructions=instructions, subtotal=subtotal, delivery_fee=delivery_fee,
                total_price=total, status=Order.Status.CONFIRMED,
            )
            for ci in cart_items:
                OrderItem.objects.create(
                    order=order, item=ci.item, bouquet=ci.bouquet,
                    name_snapshot=ci.name, quantity=ci.quantity, unit_price=ci.unit_price,
                )
                if ci.bouquet:
                    ci.bouquet.status = ci.bouquet.Status.ORDERED
                    ci.bouquet.save()

            Payment.objects.create(
                order=order, method=payment_method, amount=total,
                status=Payment.Status.PENDING if payment_method == "cash" else Payment.Status.PAID,
                card_last4=card_last4, cardholder_name=cardholder_name,
            )

            cart.status = Cart.Status.ORDERED
            cart.save()
            CartItem.objects.filter(cart=cart).delete()

        return redirect("orders:order_confirmation", order_number=order.order_number)

    return render(request, "orders/checkout.html", context)