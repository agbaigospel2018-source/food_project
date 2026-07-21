from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    # View Cart
    path(
        "",
        views.cart_detail,
        name="cart_detail",
    ),

    # Add Item to Cart
    path(
        "add/<int:menu_item_id>/",
        views.add_to_cart_view,
        name="add_to_cart",
    ),

    # Remove Item from Cart
    path(
        "remove/<int:menu_item_id>/",
        views.remove_from_cart_view,
        name="remove_from_cart",
    ),

    # Update Cart Item Quantity
    path(
        "update/<int:cart_item_id>/",
        views.update_quantity_view,
        name="update_quantity",
    ),

    # Clear Cart
    path(
        "clear/",
        views.clear_cart_view,
        name="clear_cart",
    ),
]