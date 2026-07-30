from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from datetime import datetime
from django.utils import timezone
from cart.services import get_or_create_cart

from vendors.models import Vendor

from .forms import OrderForm
from .models import Order, OrderStatus
from .services import create_order_from_cart
from django.db.models import Count, Q, Sum
from decimal import Decimal
from notifications.models import Notification, NotificationType
import json

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

    form = OrderForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            pickup_time = form.cleaned_data["pickup_time"]

            if timezone.is_naive(pickup_time):
                pickup_time = timezone.make_aware(
                    pickup_time,
                    timezone.get_current_timezone(),
                )

            try:
                order = create_order_from_cart(
                    student=request.user,
                    pickup_time=pickup_time,
                )

            except ValidationError as e:
                messages.error(request, e)

            else:
                messages.success(
                    request,
                    "Your order has been placed successfully."
                )

                return redirect(
                    "orders:order_success",
                    order_id=order.id,
                )

    context = {
        "cart": cart,
        "vendor": vendor,
        "form": form,
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
    Display all active orders placed by the logged-in student (excluding completed, cancelled, and rejected orders).
    """

    orders = (
        Order.objects
        .filter(student=request.user)
        .exclude(status__in=[OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.REJECTED])
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
    Display the details of a single order for either the student who placed it
    or the vendor owner assigned to it.
    """

    order = get_object_or_404(
        Order.objects.select_related("vendor", "student")
        .prefetch_related("items__menu_item"),
        id=order_id,
    )

    if order.student_id != request.user.id and order.vendor.owner_id != request.user.id:
        messages.error(request, "You do not have permission to view this order.")
        return redirect("orders:order_history")

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

    if order.status != OrderStatus.RECEIVED:

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

    today = timezone.localdate()

    orders = (
        Order.objects
        .filter(vendor=vendor)
        .select_related("student")
        .prefetch_related("items__menu_item")
        .order_by("-created_at")
    )

    today_orders = orders.filter(
        created_at__date=today
    )

    stats = today_orders.aggregate(
        pending_orders=Count(
            "id",
            filter=Q(status=OrderStatus.RECEIVED)
        ),
        accepted_orders=Count(
            "id",
            filter=Q(status=OrderStatus.ACCEPTED)
        ),
        preparing_orders=Count(
            "id",
            filter=Q(status=OrderStatus.PREPARING)
        ),
        ready_orders=Count(
            "id",
            filter=Q(status=OrderStatus.READY)
        ),
        completed_orders=Count(
            "id",
            filter=Q(status=OrderStatus.COMPLETED)
        ),
        rejected_orders=Count(
            "id",
            filter=Q(status=OrderStatus.REJECTED)
        ),
        cancelled_orders=Count(
            "id",
            filter=Q(status=OrderStatus.CANCELLED)
        ),
        today_revenue=Sum(
            "total_amount",
            filter=Q(status=OrderStatus.COMPLETED)
        ),
    )

    context = {
        "vendor": vendor,
        "orders": orders,
        "today_orders": today_orders.count(),
        "pending_orders": stats["pending_orders"] or 0,
        "accepted_orders": stats["accepted_orders"] or 0,
        "preparing_orders": stats["preparing_orders"] or 0,
        "ready_orders": stats["ready_orders"] or 0,
        "completed_orders": stats["completed_orders"] or 0,
        "today_revenue": stats["today_revenue"] or Decimal("0.00"),
        
        # Order Lists for template
        "pending_list": orders.filter(status=OrderStatus.RECEIVED),
        "accepted_list": orders.filter(status=OrderStatus.ACCEPTED),
        "preparing_list": orders.filter(status=OrderStatus.PREPARING),
        "ready_list": orders.filter(status=OrderStatus.READY),
        "completed_list": orders.filter(status=OrderStatus.COMPLETED),
    }

    return render(
        request,
        "vendors/vendor_orders.html",
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
    
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json'

    if is_ajax:
        try:
            data = json.loads(request.body)
            new_status = data.get("status")
        except json.JSONDecodeError:
            new_status = request.POST.get("status")
    else:
        new_status = request.POST.get("status")

    if new_status not in dict(OrderStatus.choices):
        if is_ajax:
            return JsonResponse({"error": "Invalid order status."}, status=400)
        messages.error(request, "Invalid order status.")
        return redirect("orders:vendor_orders")

    # Use model methods to update status and timestamps
    if new_status == OrderStatus.ACCEPTED:
        order.accept()
        notif_type = NotificationType.ORDER_ACCEPTED
        title = "Order Accepted"
        message = f"Your order #{order.short_id()} from {vendor.business_name} has been accepted!"
    elif new_status == OrderStatus.PREPARING:
        order.start_preparing()
        notif_type = NotificationType.ORDER_PREPARING
        title = "Order Preparing"
        message = f"Your order #{order.short_id()} is now being prepared by {vendor.business_name}."
    elif new_status == OrderStatus.READY:
        order.mark_ready()
        notif_type = NotificationType.ORDER_READY
        title = "Order Ready"
        message = f"Your order #{order.short_id()} from {vendor.business_name} is ready for pickup!"
    elif new_status == OrderStatus.COMPLETED:
        order.complete()
        notif_type = NotificationType.ORDER_COMPLETED
        title = "Order Completed"
        message = f"Your order #{order.short_id()} has been completed. Enjoy your meal!"
    elif new_status == OrderStatus.REJECTED:
        order.reject()
        notif_type = NotificationType.ORDER_REJECTED
        title = "Order Rejected"
        message = f"Unfortunately, your order #{order.short_id()} was rejected by {vendor.business_name}."
    else:
        order.status = new_status
        order.save(update_fields=["status"])
        notif_type = NotificationType.SYSTEM
        title = "Order Status Updated"
        message = f"Your order #{order.short_id()} status changed to {order.get_status_display()}."
        
    # Create notification for the student
    Notification.objects.create(
        recipient=order.student,
        notification_type=notif_type,
        title=title,
        message=message,
        order=order
    )

    if is_ajax:
        return JsonResponse({"success": True, "message": f"Order status updated to {order.get_status_display()}."})

    messages.success(request, f"Order status updated to {order.get_status_display()}.")
    return redirect("orders:vendor_orders")