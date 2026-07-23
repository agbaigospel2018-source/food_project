from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from datetime import datetime
from datetime import datetime
from cart.services import get_or_create_cart

from .models import Order
from .services import (
    create_order_from_cart,
    generate_pickup_slots,
)

# Create your views here.
@login_required
def checkout_view(request):
    """
    Display the checkout page and create an order.
    """

    cart = get_or_create_cart(request.user)

    if not cart.items.exists():
        messages.error(
            request,
            "Your cart is empty."
        )
        return redirect("cart:cart_detail")

    # Get the vendor from the first cart item
    vendor = cart.items.select_related(
        "menu_item__vendor"
    ).first().menu_item.vendor

    # Generate available pickup slots
    pickup_slots = generate_pickup_slots(vendor)

    if request.method == "POST":

        pickup_time_str = request.POST.get("pickup_time")

        try:
            # Convert the submitted value into a time object
            pickup_time = datetime.strptime(
                pickup_time_str,
                "%I:%M %p"
             ).time()

            order = create_order_from_cart(
                student=request.user,
                pickup_time=pickup_time,
            )

            messages.success(
                request,
                "Your order has been placed successfully."
            )

            return redirect(
                "orders:order_success",
                order_id=order.id,
            )

        except ValidationError as e:
            messages.error(request, e)

        except ValueError:
            messages.error(
                request,
                "Please select a valid pickup time."
            )

    context = {
        "cart": cart,
        "vendor": vendor,
        "pickup_slots": pickup_slots,
    }

    return render(
        request,
        "orders/checkout.html",
        context,
    )
    
    
@login_required
def order_success_view(request, order_id):
    """
    Display a successful order confirmation.
    """

    order = get_object_or_404(
        Order,
        id=order_id,
        student=request.user,
    )

    return render(
        request,
        "orders/order_success.html",
        {
            "order": order,
        },
    )
    
@login_required
def order_history_view(request):
    """
    Display all orders placed by the logged-in student.
    """

    orders = (
        Order.objects
        .filter(student=request.user)
        .select_related("vendor")
        .prefetch_related("items")
        .order_by("-created_at")
    )

    context = {
        "orders": orders,
    }

    return render(
        request,
        "orders/order_history.html",
        context,
    )
    
@login_required
@login_required
def vendor_orders_view(request, order_id):
    """
    Display the details of a single order belonging to the logged-in student.
    """

    order = get_object_or_404(
        Order.objects.select_related("vendor", "student")
        .prefetch_related("items__menu_item"),
        id=order_id,
        student=request.user,
    )

    context = {
        "order": order,
    }

    return render(
        request,
        "orders/order_detail.html",
        context,
    )
    
@login_required
def cancel_order_view(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        student=request.user,
    )

    if order.status != Order.PENDING:

        messages.error(
            request,
            "This order can no longer be cancelled."
        )

        return redirect(
            "orders:order_detail",
            order_id=order.id,
        )

    order.status = Order.CANCELLED
    order.save(update_fields=["status"])

    messages.success(
        request,
        "Order cancelled successfully."
    )

    return redirect(
        "orders:order_history",
    )