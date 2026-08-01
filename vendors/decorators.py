from functools import wraps
from django.shortcuts import get_object_or_404
from .models import Vendor

def vendor_required(view_func):
    """
    Decorator for views that checks that the user is logged in and is a vendor.
    Passes the vendor object to the view.
    Assumes @login_required is also used.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        vendor = get_object_or_404(Vendor, owner=request.user)
        return view_func(request, vendor, *args, **kwargs)
    return _wrapped_view
