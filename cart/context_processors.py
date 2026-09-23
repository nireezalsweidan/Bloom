from decimal import Decimal
from .models import Cart


def cart_badge(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user, status=Cart.Status.ACTIVE).first()
        if cart:
            return {"cart_badge_count": cart.total_quantity, "cart_badge_total": cart.total_price}
    return {"cart_badge_count": 0, "cart_badge_total": Decimal("0.00")}