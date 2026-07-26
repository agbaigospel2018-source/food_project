from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Vendor
from .forms import VendorForm


# ==========================================
# Public Views
# ==========================================

def vendor_list(request):
    """
    Display all vendors.
    """

    vendors = Vendor.objects.all().order_by("business_name")

    # Search
    query = request.GET.get("q")

    if query:
        vendors = vendors.filter(
            Q(business_name__icontains=query) |
            Q(location__icontains=query) |
            Q(description__icontains=query)
        )

    # Filter
    status = request.GET.get("status")

    if status == "open":
        vendors = vendors.filter(is_open=True)

    elif status == "closed":
        vendors = vendors.filter(is_open=False)

    # Pagination
    paginator = Paginator(vendors, 9)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    context = {
        "vendors": page_obj,
        "page_obj": page_obj,
        "total_vendors": Vendor.objects.count(),
        "open_vendors": Vendor.objects.filter(is_open=True).count(),
        "page_title": "Discover Amazing Restaurants",
        "page_subtitle": "Order ahead from your favorite campus restaurants.",
    }

    return render(
        request,
        "vendors/vendor_list.html",
        context,
    )


def vendor_detail(request, pk):
    """
    Public restaurant page.
    """

    vendor = get_object_or_404(
        Vendor,
        pk=pk
    )

    # Future integrations
    categories = []
    menu_items = []
    reviews = []

    context = {
        "vendor": vendor,
        "categories": categories,
        "menu_items": menu_items,
        "reviews": reviews,
    }

    return render(
        request,
        "vendors/vendor_detail.html",
        context,
    )


# ==========================================
# Vendor Dashboard
# ==========================================

@login_required
def vendor_dashboard(request):

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )

    context = {
        "vendor": vendor,
        "total_orders": 0,
        "pending_orders": 0,
        "completed_orders": 0,
        "today_orders": 0,
        "revenue": 0,
    }

    return render(
        request,
        "vendors/dashboard/dashboard.html",
        context,
    )


@login_required
def vendor_profile(request):

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )

    context = {
        "vendor": vendor
    }

    return render(
        request,
        "vendors/dashboard/profile.html",
        context,
    )


@login_required
def create_vendor(request):

    if hasattr(request.user, "vendor_profile"):

        messages.info(
            request,
            "You already have a vendor profile."
        )

        return redirect(
            "vendors:vendor_dashboard"
        )

    if request.method == "POST":

        form = VendorForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            vendor = form.save(
                commit=False
            )

            vendor.owner = request.user

            vendor.save()

            messages.success(
                request,
                "Vendor profile created successfully."
            )

            return redirect(
                "vendors:vendor_dashboard"
            )

    else:

        form = VendorForm()

    context = {
        "form": form
    }

    return render(
        request,
        "vendors/dashboard/create_vendor.html",
        context,
    )


@login_required
def edit_vendor(request):

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )

    if request.method == "POST":

        form = VendorForm(
            request.POST,
            request.FILES,
            instance=vendor
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Vendor profile updated successfully."
            )

            return redirect(
                "vendors:vendor_profile"
            )

    else:

        form = VendorForm(
            instance=vendor
        )

    context = {
        "form": form,
        "vendor": vendor,
    }

    return render(
        request,
        "vendors/dashboard/edit_profile.html",
        context,
    )


@login_required
def vendor_orders(request):

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )

    orders = []

    context = {
        "vendor": vendor,
        "orders": orders,
    }

    return render(
        request,
        "vendors/dashboard/vendor_orders.html",
        context,
    )


@login_required
def analytics(request):

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )

    context = {
        "vendor": vendor,
    }

    return render(
        request,
        "vendors/dashboard/analytics.html",
        context,
    )


@login_required
def business_hours(request):

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )

    context = {
        "vendor": vendor,
    }

    return render(
        request,
        "vendors/dashboard/business_hours.html",
        context,
    )


@login_required
def settings(request):

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )

    context = {
        "vendor": vendor,
    }

    return render(
        request,
        "vendors/dashboard/settings.html",
        context,
    )


@login_required
def toggle_vendor_status(request):

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )

    vendor.is_open = not vendor.is_open

    vendor.save()

    if vendor.is_open:

        messages.success(
            request,
            "Your restaurant is now OPEN."
        )

    else:

        messages.warning(
            request,
            "Your restaurant is now CLOSED."
        )

    return redirect(
        "vendors:vendor_profile"
    )


@login_required
def delete_vendor(request):

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )

    if request.method == "POST":

        vendor.delete()

        messages.success(
            request,
            "Vendor profile deleted successfully."
        )

        return redirect(
            "home"
        )

    context = {
        "vendor": vendor
    }

    return render(
        request,
        "vendors/dashboard/delete_vendor.html",
        context,
    )