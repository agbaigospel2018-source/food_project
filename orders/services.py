from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from cart.models import Cart
from cart.services import clear_cart

from .models import Order, OrderItem
from datetime import datetime, timedelta


def validate_cart(cart, pickup_time):
    """
    Validate the student's cart before checkout.
    """

    if not cart.items.exists():
        raise ValidationError("Your cart is empty.")

    first_item = (
        cart.items
        .select_related("menu_item__vendor")
        .first()
    )

    vendor = first_item.menu_item.vendor

    # Vendor currently accepting orders
    if not vendor.is_open:
        raise ValidationError(
            f"{vendor.business_name} is currently closed."
        )

    # Pickup time validation
    if pickup_time:
        pickup_time_value = (
            pickup_time.time()
            if isinstance(pickup_time, datetime)
            else pickup_time
        )

        if vendor.opening_time < vendor.closing_time:
            if (
                pickup_time_value < vendor.opening_time
                or pickup_time_value > vendor.closing_time
            ):
                raise ValidationError(
                    "Selected pickup time is outside the vendor's operating hours."
                )
        else:
            # Vendor closes after midnight
            if not (
                pickup_time_value >= vendor.opening_time
                or pickup_time_value <= vendor.closing_time
            ):
                raise ValidationError(
                    "Selected pickup time is outside the vendor's operating hours."
                )

    for item in cart.items.select_related(
        "menu_item",
        "menu_item__vendor",
    ):

        menu_item = item.menu_item

        # Item hidden
        if not menu_item.is_active:
            raise ValidationError(
                f"{menu_item.name} is no longer available."
            )

        # Item unavailable
        if not menu_item.is_available_now:
            raise ValidationError(
                f"{menu_item.name} is currently unavailable."
            )

        # Vendor mismatch
        if menu_item.vendor_id != vendor.id:
            raise ValidationError(
                "Your cart contains items from different vendors."
            )

        # Stock validation
        if (
            menu_item.stock_quantity is not None
            and item.quantity > menu_item.stock_quantity
        ):
            raise ValidationError(
                f"Only {menu_item.stock_quantity} {menu_item.name} remaining."
            )


@transaction.atomic
def create_order_from_cart(student, pickup_time):
    """
    Convert the student's active cart into an order.
    """

    cart = (
        Cart.objects
        .select_for_update()
        .prefetch_related(
            "items__menu_item",
            "items__menu_item__vendor",
        )
        .get(student=student)
    )

    # Validate everything before creating the order
    validate_cart(cart, pickup_time)

    first_item = cart.items.first()
    vendor = first_item.menu_item.vendor

    # Create the order
    order = Order.objects.create(
        student=student,
        vendor=vendor,
        pickup_time=pickup_time,
    )

    # Copy cart items into order items
    order_items = []

    for cart_item in cart.items.all():
        unit_price = cart_item.menu_item.current_price

        order_items.append(
            OrderItem(
                order=order,
                menu_item=cart_item.menu_item,
                quantity=cart_item.quantity,
                unit_price=unit_price,
                subtotal=cart_item.quantity * unit_price,
            )
        )

    # Bulk insert (faster than creating one by one)
    OrderItem.objects.bulk_create(order_items)

    # Copy the cart total
    order.total_amount = cart.total_amount
    order.save(update_fields=["total_amount"])

    # Empty the cart
    clear_cart(student)

    return order

def generate_pickup_slots(vendor, interval=15, prep_buffer=20):
    """
    Generate available pickup slots for a vendor.

    Returns:
        [
            {"value": "12:30", "label": "12:30 PM"},
            {"value": "12:45", "label": "12:45 PM"},
            ...
        ]
    """

    today = datetime.today().date()

    start = datetime.combine(today, vendor.opening_time)
    end = datetime.combine(today, vendor.closing_time)

    # Handle vendors that close after midnight
    if end < start:
        end += timedelta(days=1)

    # Don't allow pickup immediately after ordering
    earliest_pickup = datetime.now() + timedelta(minutes=prep_buffer)

    slots = []

    while start <= end:

        # Only include future slots
        if start >= earliest_pickup:
            slots.append(
                {
                    "value": start.strftime("%H:%M"),
                    "label": start.strftime("%I:%M %p").lstrip("0"),
                }
            )

        start += timedelta(minutes=interval)

    return slots