from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from datetime import datetime
from datetime import datetime
from cart.services import get_or_create_cart

from vendors.models import Vendor

from .models import Order, OrderStatus
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
def order_detail_view(request, order_id):
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


@login_required
def vendor_orders_view(request):
    """
    Display all incoming orders for the logged-in vendor.
    """

    vendor = get_object_or_404(
        Vendor,
        owner=request.user,
    )

    orders = (
        Order.objects
        .filter(vendor=vendor)
        .select_related("student")
        .prefetch_related("items__menu_item")
        .order_by("-created_at")
    )

    context = {
        "vendor": vendor,
        "orders": orders,
    }

    return render(
        request,
        "orders/vendor_orders.html",
        context,
    )


@login_required
@require_POST
def update_order_status_view(request, order_id):
    """
    Allow a vendor to update the status of an order.
    """

    vendor = get_object_or_404(
        Vendor,
        owner=request.user,
    )

    order = get_object_or_404(
        Order,
        id=order_id,
        vendor=vendor,
    )

    new_status = request.POST.get("status")

    if new_status not in dict(OrderStatus.choices):
        messages.error(
            request,
            "Invalid order status."
        )
        return redirect(
            "orders:vendor_orders",
        )

    order.status = new_status
    order.save(update_fields=["status"])

    messages.success(
        request,
        f"Order status updated to {order.get_status_display()}."
    )

    return redirect(
        "orders:vendor_orders",
    )