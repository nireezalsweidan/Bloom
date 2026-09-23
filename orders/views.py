from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from cart.models import Cart, CartItem
from payments.models import Payment
from .models import Order, OrderItem

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
    return render(request, "orders/order_list.html", {"orders": request.user.orders.all()})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, "orders/order_detail.html", {"order": order})