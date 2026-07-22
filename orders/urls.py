from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [

    # ==========================
    # Student Views
    # ==========================

    # Checkout
    path(
        "checkout/",
        views.checkout_view,
        name="checkout",
    ),

    # Order Success
    path(
        "success/<uuid:order_id>/",
        views.order_success_view,
        name="order_success",
    ),

    # Order History
    path(
        "history/",
        views.order_history_view,
        name="order_history",
    ),

    # Order Details
    path(
        "<uuid:order_id>/",
        views.order_detail_view,
        name="order_detail",
    ),

    # Cancel Order
    path(
        "<uuid:order_id>/cancel/",
        views.cancel_order_view,
        name="cancel_order",
    ),

    # ==========================
    # Vendor Views
    # ==========================

    # Vendor Dashboard
    path(
        "vendor/",
        views.vendor_orders_view,
        name="vendor_orders",
    ),

    # Update Order Status
    path(
        "vendor/<uuid:order_id>/status/",
        views.update_order_status_view,
        name="update_order_status",
    ),
]