from django.urls import path
from . import views

app_name = "vendors"

urlpatterns = [

    # ==========================================
    # Student Views
    # ==========================================

    path(
        "",
        views.vendor_list,
        name="vendor_list"
    ),

    path(
        "<int:pk>/",
        views.vendor_detail,
        name="vendor_detail"
    ),

    # ==========================================
    # Vendor Management
    # ==========================================

    path(
        "dashboard/",
        views.vendor_dashboard,
        name="vendor_dashboard"
    ),

    path(
        "profile/",
        views.vendor_profile,
        name="vendor_profile"
    ),

    path(
        "create/",
        views.create_vendor,
        name="create_vendor"
    ),

    path(
        "edit/",
        views.edit_vendor,
        name="edit_vendor"
    ),

    path(
        "toggle-status/",
        views.toggle_vendor_status,
        name="toggle_vendor_status"
    ),

    path(
        "delete/",
        views.delete_vendor,
        name="delete_vendor"
    ),

]