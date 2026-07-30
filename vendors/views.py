from datetime import timedelta

from django.db.models import (
    Sum,
    Count,
    Avg,
    F,
    DecimalField,
)

from django.db.models.functions import (
    TruncDate,
    ExtractHour,
)

from django.utils import timezone

from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth import login

User = get_user_model()

from .models import Vendor
from .forms import VendorForm, BusinessHoursForm
from menu.models import MenuItem
from orders.models import Order, OrderStatus, OrderItem
from notifications.models import NotificationPreference


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
            suggestions.append(
                {
                    "label": vendor.business_name,
                    "value": vendor.business_name,
                    "url": reverse("vendors:vendor_detail", kwargs={"pk": vendor.pk}),
                    "meta": vendor.location,
                }
            )

    return JsonResponse({"suggestions": suggestions})


def vendor_detail(request, pk):

    vendor = get_object_or_404(
        Vendor,
        pk=pk
    )

    menu_items = MenuItem.objects.filter(
        vendor=vendor,
        is_available=True
    ).select_related(
        "category"
    )

    categories = (
        menu_items
        .values_list("category__name", flat=True)
        .distinct()
    )

    context = {
        "vendor": vendor,
        "menu_items": menu_items,
        "categories": categories,
        "menu_count": menu_items.count(),
    }

    return render(
        request,
        "vendors/vendor_detail.html",
        context
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

    orders = (
        Order.objects
        .filter(vendor=vendor)
        .select_related("student")
        .order_by("-created_at")
    )

    today_start = timezone.localtime(timezone.now()).replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timezone.timedelta(days=1)

    today_orders = orders.filter(created_at__gte=today_start, created_at__lt=today_end).count()
    pending_orders = orders.filter(status=OrderStatus.RECEIVED).count()
    completed_orders = orders.filter(status=OrderStatus.COMPLETED).count()
    revenue = sum((order.total_amount for order in orders.filter(status=OrderStatus.COMPLETED)), start=0)

    context = {
        "vendor": vendor,
        "total_orders": orders.count(),
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
        "today_orders": today_orders,
        "revenue": f"{revenue:.2f}",
        "recent_orders": orders[:5],
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )


@login_required
def vendor_profile(request):

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )

    orders = (
        Order.objects
        .filter(vendor=vendor)
        .select_related("student")
        .order_by("-created_at")
    )

    recent_orders = orders[:5]

    total_orders = orders.count()

    completed_orders = orders.filter(
        status=OrderStatus.COMPLETED
    ).count()

    active_orders = orders.exclude(
        status__in=[
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        ]
    ).count()

    total_revenue = sum(
        (
            order.total_amount
            for order in orders.filter(
                status=OrderStatus.COMPLETED
            )
        ),
        start=0
    )

    menu_items = MenuItem.objects.filter(
        vendor=vendor
    )

    context = {
        "vendor": vendor,

        "menu_items": menu_items,

        "menu_count": menu_items.count(),

        "total_orders": total_orders,

        "completed_orders": completed_orders,

        "active_orders": active_orders,

        "total_revenue": total_revenue,

        "recent_orders": recent_orders,
    }

    return render(
        request,
        "dashboard/profile.html",
        context,
    )


def create_vendor(request):

    user = request.user
    pending_user_id = request.session.get('pending_vendor_user_id')

    if not user.is_authenticated:
        if pending_user_id:
            try:
                user = User.objects.get(id=pending_user_id)
            except User.DoesNotExist:
                return redirect('login')
        else:
            return redirect('login')

    if hasattr(user, "vendor_profile"):
        if request.user.is_authenticated:
            messages.info(
                request,
                "You already have a vendor profile."
            )
            return redirect("vendors:vendor_dashboard")
        else:
            login(request, user)
            if 'pending_vendor_user_id' in request.session:
                del request.session['pending_vendor_user_id']
            return redirect("vendors:vendor_dashboard")

    if request.method == "POST":

        form = VendorForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            vendor = form.save(
                commit=False
            )

            vendor.owner = user

            vendor.save()

            messages.success(
                request,
                "Vendor profile created successfully."
            )
            
            if not request.user.is_authenticated:
                login(request, user)
                if 'pending_vendor_user_id' in request.session:
                    del request.session['pending_vendor_user_id']

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
        "dashboard/create_vendor.html",
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
        "dashboard/edit_profile.html",
        context,
    )


@login_required
def vendor_orders(request):

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
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
            filter=Q(status="pending")
        ),

        accepted_orders=Count(
            "id",
            filter=Q(status="accepted")
        ),

        preparing_orders=Count(
            "id",
            filter=Q(status="preparing")
        ),

        ready_orders=Count(
            "id",
            filter=Q(status="ready")
        ),

        completed_orders=Count(
            "id",
            filter=Q(status="completed")
        ),

        rejected_orders=Count(
            "id",
            filter=Q(status="rejected")
        ),

        cancelled_orders=Count(
            "id",
            filter=Q(status="cancelled")
        ),

        today_revenue=Sum(
            "total_amount",
            filter=Q(status="completed")
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

        "rejected_orders": stats["rejected_orders"] or 0,

        "cancelled_orders": stats["cancelled_orders"] or 0,

        "today_revenue": stats["today_revenue"] or Decimal("0.00"),

    }

    return render(
        request,
        "vendors/vendor_orders.html",
        context,
    )


@login_required
def analytics(request):

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )

    now = timezone.now()
    today = now.date()

    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    last_30_days = today - timedelta(days=29)

    orders = (
        Order.objects
        .filter(vendor=vendor)
        .select_related("student")
    )

    # ==========================================
    # Revenue
    # ==========================================

    today_revenue = (
        orders.filter(
            created_at__date=today,
            status=OrderStatus.COMPLETED
        ).aggregate(
            total=Sum("total_amount")
        )["total"] or 0
    )

    weekly_revenue = (
        orders.filter(
            created_at__date__gte=week_start,
            status=OrderStatus.COMPLETED
        ).aggregate(
            total=Sum("total_amount")
        )["total"] or 0
    )

    monthly_revenue = (
        orders.filter(
            created_at__date__gte=month_start,
            status=OrderStatus.COMPLETED
        ).aggregate(
            total=Sum("total_amount")
        )["total"] or 0
    )

    lifetime_revenue = (
        orders.filter(
            status=OrderStatus.COMPLETED
        ).aggregate(
            total=Sum("total_amount")
        )["total"] or 0
    )

    # ==========================================
    # Orders
    # ==========================================

    today_orders = orders.filter(
        created_at__date=today
    ).count()

    weekly_orders = orders.filter(
        created_at__date__gte=week_start
    ).count()

    monthly_orders = orders.filter(
        created_at__date__gte=month_start
    ).count()

    total_orders = orders.count()

    # ==========================================
    # Status Counts
    # ==========================================

    pending_orders = orders.filter(
        status=OrderStatus.RECEIVED
    ).count()

    accepted_orders = orders.filter(
        status=OrderStatus.ACCEPTED
    ).count()

    preparing_orders = orders.filter(
        status=OrderStatus.PREPARING
    ).count()

    ready_orders = orders.filter(
        status=OrderStatus.READY
    ).count()

    completed_orders = orders.filter(
        status=OrderStatus.COMPLETED
    ).count()

    cancelled_orders = orders.filter(
        status=OrderStatus.CANCELLED
    ).count()

    rejected_orders = orders.filter(
        status=OrderStatus.REJECTED
    ).count()

    # ==========================================
    # Average Order Value
    # ==========================================

    average_order_value = 0

    if completed_orders:

        average_order_value = (
            lifetime_revenue / completed_orders
        )

    # ==========================================
    # Revenue Chart (Last 30 Days)
    # ==========================================

    revenue_chart = (

        orders.filter(
            created_at__date__gte=last_30_days,
            status=OrderStatus.COMPLETED
        )

        .annotate(
            day=TruncDate("created_at")
        )

        .values("day")

        .annotate(
            revenue=Sum("total_amount")
        )

        .order_by("day")

    )

    # ==========================================
    # Orders Per Day
    # ==========================================

    order_chart = (

        orders.filter(
            created_at__date__gte=last_30_days
        )

        .annotate(
            day=TruncDate("created_at")
        )

        .values("day")

        .annotate(
            total=Count("id")
        )

        .order_by("day")

    )

    # ==========================================
    # Top Selling Menu Items
    # ==========================================

    top_items = (

        OrderItem.objects

        .filter(
            order__vendor=vendor,
            order__status=OrderStatus.COMPLETED,
        )

        .values(
            "menu_item__name"
        )

        .annotate(
            quantity_sold=Sum("quantity"),
            revenue=Sum("subtotal"),
        )

        .order_by("-quantity_sold")[:5]

    )

    # ==========================================
    # Peak Ordering Hour
    # ==========================================

    peak_hour = (

        orders

        .annotate(
            hour=ExtractHour("created_at")
        )

        .values("hour")

        .annotate(
            total=Count("id")
        )

        .order_by("-total")

        .first()

    )

    # ==========================================
    # Completion & Cancellation Rates
    # ==========================================

    completion_rate = 0
    cancellation_rate = 0

    if total_orders:

        completion_rate = round(
            (completed_orders / total_orders) * 100,
            1
        )

        cancellation_rate = round(
            (cancelled_orders / total_orders) * 100,
            1
        )

    # ==========================================
    # Revenue Growth
    # ==========================================

    previous_week_start = week_start - timedelta(days=7)
    previous_week_end = week_start

    previous_week_revenue = (

        orders.filter(
            created_at__date__gte=previous_week_start,
            created_at__date__lt=previous_week_end,
            status=OrderStatus.COMPLETED,
        )

        .aggregate(
            total=Sum("total_amount")
        )["total"] or 0

    )

    revenue_growth = 0

    if previous_week_revenue:

        revenue_growth = round(
            (
                (weekly_revenue - previous_week_revenue)
                / previous_week_revenue
            ) * 100,
            1
        )

    # ==========================================
    # Recent Orders
    # ==========================================

    recent_orders = orders.order_by(
        "-created_at"
    )[:10]

    context = {

        "vendor": vendor,

        "today_revenue": today_revenue,
        "weekly_revenue": weekly_revenue,
        "monthly_revenue": monthly_revenue,
        "lifetime_revenue": lifetime_revenue,

        "today_orders": today_orders,
        "weekly_orders": weekly_orders,
        "monthly_orders": monthly_orders,
        "total_orders": total_orders,

        "pending_orders": pending_orders,
        "accepted_orders": accepted_orders,
        "preparing_orders": preparing_orders,
        "ready_orders": ready_orders,
        "completed_orders": completed_orders,
        "cancelled_orders": cancelled_orders,
        "rejected_orders": rejected_orders,

        "average_order_value": average_order_value,

        "completion_rate": completion_rate,
        "cancellation_rate": cancellation_rate,

        "peak_hour": peak_hour,
        "revenue_growth": revenue_growth,

        "top_items": top_items,

        "revenue_chart": revenue_chart,
        "order_chart": order_chart,

        "recent_orders": recent_orders,

    }

    return render(
        request,
        "dashboard/analytics.html",
        context,
    )
   
   


@login_required
def business_hours(request):

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )

    if request.method == "POST":

        form = BusinessHoursForm(
            request.POST,
            instance=vendor
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Business hours updated successfully."
            )

            return redirect(
                "vendors:business_hours"
            )

    else:

        form = BusinessHoursForm(
            instance=vendor
        )

    context = {

        "vendor": vendor,
        "form": form,

    }

    return render(
        request,
        "dashboard/business_hours.html",
        context,
    )


@login_required
def settings(request):

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )

    prefs, _ = NotificationPreference.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        prefs.notify_new_orders = "notify_new_orders" in request.POST
        prefs.notify_status     = "notify_status"     in request.POST
        prefs.notify_reviews    = "notify_reviews"    in request.POST
        prefs.notify_push       = "notify_push"       in request.POST
        prefs.notify_email      = "notify_email"      in request.POST
        prefs.notify_marketing  = "notify_marketing"  in request.POST

        prefs.save()

        messages.success(
            request,
            "Notification preferences saved successfully."
        )

        return redirect("vendors:settings")

    context = {
        "vendor": vendor,
        "preferences": prefs,
    }

    return render(
        request,
        "dashboard/settings.html",
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

        user = request.user
        user.delete()

        messages.success(
            request,
            "Vendor profile and account deleted successfully."
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