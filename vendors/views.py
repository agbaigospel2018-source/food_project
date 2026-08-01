from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST

from .models import Vendor
from .forms import VendorForm, BusinessHoursForm
from menu.models import MenuItem
from orders.models import Order, OrderStatus, OrderItem
from notifications.models import NotificationPreference

from .services import get_vendor_analytics
from .decorators import vendor_required

User = get_user_model()


# ==========================================
# Public Views
# ==========================================

def vendor_list(request):
    """Display all vendors."""
    vendors = Vendor.objects.all().order_by("business_name")

    query = request.GET.get("q")
    if query:
        vendors = vendors.filter(
            Q(business_name__icontains=query) |
            Q(location__icontains=query) |
            Q(description__icontains=query)
        )

    status = request.GET.get("status")
    if status == "open":
        vendors = vendors.filter(is_open=True)
    elif status == "closed":
        vendors = vendors.filter(is_open=False)

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
    return render(request, "vendors/vendor_list.html", context)


def vendor_search_suggestions(request):
    query = (request.GET.get("q") or "").strip()
    suggestions = []

    if query:
        vendors = Vendor.objects.filter(
            Q(business_name__icontains=query) |
            Q(location__icontains=query) |
            Q(description__icontains=query)
        )[:8]

        for vendor in vendors:
            suggestions.append({
                "label": vendor.business_name,
                "value": vendor.business_name,
                "url": reverse("vendors:vendor_detail", kwargs={"pk": vendor.pk}),
                "meta": vendor.location,
            })

    return JsonResponse({"suggestions": suggestions})


def vendor_detail(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    menu_items = MenuItem.objects.filter(vendor=vendor, is_available=True).select_related("category")
    categories = menu_items.values_list("category__name", flat=True).distinct()

    context = {
        "vendor": vendor,
        "menu_items": menu_items,
        "categories": categories,
        "menu_count": menu_items.count(),
    }
    return render(request, "vendors/vendor_detail.html", context)


# ==========================================
# Vendor Dashboard
# ==========================================

@login_required
@vendor_required
def vendor_dashboard(request, vendor):
    orders = Order.objects.filter(vendor=vendor).select_related("student").order_by("-created_at")

    today_start = timezone.localtime(timezone.now()).replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timezone.timedelta(days=1)

    today_orders = orders.filter(created_at__gte=today_start, created_at__lt=today_end).count()
    pending_orders = orders.filter(status=OrderStatus.RECEIVED).count()
    completed_orders = orders.filter(status=OrderStatus.COMPLETED)
    
    # N+1 / Memory issue fixed: calculating revenue in database
    revenue = completed_orders.aggregate(total=Sum('total_amount'))['total'] or 0

    context = {
        "vendor": vendor,
        "total_orders": orders.count(),
        "pending_orders": pending_orders,
        "completed_orders": completed_orders.count(),
        "today_orders": today_orders,
        "revenue": f"{revenue:.2f}",
        "recent_orders": orders[:5],
    }
    return render(request, "dashboard/dashboard.html", context)


@login_required
@vendor_required
def vendor_profile(request, vendor):
    orders = Order.objects.filter(vendor=vendor).select_related("student").order_by("-created_at")

    recent_orders = orders[:5]
    total_orders = orders.count()
    completed_orders = orders.filter(status=OrderStatus.COMPLETED)
    
    active_orders = orders.exclude(
        status__in=[OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.REJECTED]
    ).count()

    # N+1 / Memory issue fixed
    total_revenue = completed_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    menu_items = MenuItem.objects.filter(vendor=vendor)

    context = {
        "vendor": vendor,
        "menu_items": menu_items,
        "menu_count": menu_items.count(),
        "total_orders": total_orders,
        "completed_orders": completed_orders.count(),
        "active_orders": active_orders,
        "total_revenue": total_revenue,
        "recent_orders": recent_orders,
    }
    return render(request, "dashboard/profile.html", context)


@login_required
def create_vendor(request):
    if hasattr(request.user, "vendor_profile"):
        messages.info(request, "You already have a vendor profile.")
        return redirect("vendors:vendor_dashboard")

    if request.method == "POST":
        form = VendorForm(request.POST, request.FILES)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.owner = request.user
            vendor.save()
            messages.success(request, "Vendor profile created successfully.")
            return redirect("vendors:vendor_dashboard")
    else:
        form = VendorForm()

    context = {"form": form}
    return render(request, "dashboard/create_vendor.html", context)


@login_required
@vendor_required
def edit_vendor(request, vendor):
    if request.method == "POST":
        form = VendorForm(request.POST, request.FILES, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, "Vendor profile updated successfully.")
            return redirect("vendors:vendor_profile")
    else:
        form = VendorForm(instance=vendor)

    context = {
        "form": form,
        "vendor": vendor,
    }
    return render(request, "dashboard/edit_profile.html", context)


@login_required
@vendor_required
def vendor_orders(request, vendor):
    today = timezone.localdate()
    orders = Order.objects.filter(vendor=vendor).select_related("student").prefetch_related("items__menu_item").order_by("-created_at")
    today_orders = orders.filter(created_at__date=today)

    stats = today_orders.aggregate(
        pending_orders=Count("id", filter=Q(status="pending")),
        accepted_orders=Count("id", filter=Q(status="accepted")),
        preparing_orders=Count("id", filter=Q(status="preparing")),
        ready_orders=Count("id", filter=Q(status="ready")),
        completed_orders=Count("id", filter=Q(status="completed")),
        rejected_orders=Count("id", filter=Q(status="rejected")),
        cancelled_orders=Count("id", filter=Q(status="cancelled")),
        today_revenue=Sum("total_amount", filter=Q(status="completed")),
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
        "rejected_orders": stats["rejected_orders"] or 0,
        "cancelled_orders": stats["cancelled_orders"] or 0,
        "today_revenue": stats["today_revenue"] or Decimal("0.00"),
    }
    return render(request, "vendors/vendor_orders.html", context)


@login_required
@vendor_required
def analytics(request, vendor):
    context = get_vendor_analytics(vendor)
    context["vendor"] = vendor
    return render(request, "dashboard/analytics.html", context)


@login_required
@vendor_required
def business_hours(request, vendor):
    if request.method == "POST":
        form = BusinessHoursForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, "Business hours updated successfully.")
            return redirect("vendors:business_hours")
    else:
        form = BusinessHoursForm(instance=vendor)

    context = {
        "vendor": vendor,
        "form": form,
    }
    return render(request, "dashboard/business_hours.html", context)


@login_required
@vendor_required
def settings(request, vendor):
    prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)

    if request.method == "POST":
        prefs.notify_new_orders = "notify_new_orders" in request.POST
        prefs.notify_status = "notify_status" in request.POST
        prefs.notify_reviews = "notify_reviews" in request.POST
        prefs.notify_push = "notify_push" in request.POST
        prefs.notify_email = "notify_email" in request.POST
        prefs.notify_marketing = "notify_marketing" in request.POST
        prefs.save()
        messages.success(request, "Notification preferences saved successfully.")
        return redirect("vendors:settings")

    context = {
        "vendor": vendor,
        "preferences": prefs,
    }
    return render(request, "dashboard/settings.html", context)


@require_POST
@login_required
@vendor_required
def toggle_vendor_status(request, vendor):
    vendor.is_open = not vendor.is_open
    vendor.save()

    if vendor.is_open:
        messages.success(request, "Your restaurant is now OPEN.")
    else:
        messages.warning(request, "Your restaurant is now CLOSED.")

    return redirect(request.META.get("HTTP_REFERER", "vendors:vendor_profile"))


@login_required
@vendor_required
def delete_vendor(request, vendor):
    if request.method == "POST":
        user = request.user
        user.delete()
        messages.success(request, "Vendor profile and account deleted successfully.")
        return redirect("home")

    context = {"vendor": vendor}
    return render(request, "vendors/dashboard/delete_vendor.html", context)
