from django.shortcuts import render

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from.models import CartItem, Cart
from django.views.decorators.http import require_POST

from menu.models import MenuItem
from .services import (
    add_to_cart,
    clear_cart,
    get_or_create_cart,
    remove_from_cart,
    update_cart_item_quantity,
)

# Create your views here.
def add_to_cart_view(request, menu_item_id):
    """
    Add a menu item to the student's cart.
    """

    menu_item = get_object_or_404(
        MenuItem,
        pk=menu_item_id,
        is_active=True,
    )

    try:
        add_to_cart(
            student=request.user,
            menu_item=menu_item,
            quantity=1,
        )

        messages.success(
            request,
            f"{menu_item.name} was added to your cart."
        )

    except ValidationError as e:
        messages.error(
            request,
            str(e)
        )

    return redirect(request.META.get("HTTP_REFERER", "menu:vendor_list"))

@login_required
def cart_detail(request):
    cart = get_or_create_cart(request.user)

    return render(
        request,
        "cart/cart_detail.html",
        {
            "cart": cart,
        },
    )
    
@require_POST
@login_required
def add_to_cart_view(request, menu_item_id):

    menu_item = get_object_or_404(
        MenuItem,
        pk=menu_item_id,
        is_active=True,
    )

    try:
        add_to_cart(
            student=request.user,
            menu_item=menu_item,
        )

        messages.success(
            request,
            f"{menu_item.name} added to your cart."
        )

    except ValidationError as e:
        messages.error(request, str(e))

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "menu:vendor_list",
        )
    )
    
@require_POST
@login_required
def remove_from_cart_view(request, menu_item_id):

    menu_item = get_object_or_404(
        MenuItem,
        pk=menu_item_id,
    )

    remove_from_cart(
        request.user,
        menu_item,
    )

    messages.success(
        request,
        f"{menu_item.name} removed from your cart."
    )

    return redirect("cart:cart_detail")

@require_POST
@login_required
def update_quantity_view(request, cart_item_id):

    cart_item = get_object_or_404(
        CartItem,
        pk=cart_item_id,
        cart__student=request.user,
    )

    quantity = int(
        request.POST.get(
            "quantity",
            1,
        )
    )

    update_cart_item_quantity(
        cart_item,
        quantity,
    )

    messages.success(
        request,
        "Cart updated successfully."
    )

    return redirect("cart:cart_detail")

@require_POST
@login_required
def clear_cart_view(request):

    clear_cart(request.user)

    messages.success(
        request,
        "Your cart has been cleared."
    )

    return redirect("cart:cart_detail")