from django.apps import apps
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404


def get_vendor_model():
    return apps.get_model(getattr(settings, "MENU_VENDOR_MODEL", "vendors.Vendor"))


def user_can_manage_vendor(user, vendor):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    for attr in ("user", "owner", "manager"):
        if getattr(vendor, f"{attr}_id", None) == user.id:
            return True
    return False


def get_managed_vendor_or_403(user, vendor_pk):
    vendor = get_object_or_404(get_vendor_model(), pk=vendor_pk)
    if not user_can_manage_vendor(user, vendor):
        raise PermissionDenied("You do not have permission to manage this vendor menu.")
    return vendor
