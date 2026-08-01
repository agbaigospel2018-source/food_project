from datetime import timedelta
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, ExtractHour
from django.utils import timezone
from orders.models import Order, OrderStatus, OrderItem

def get_vendor_analytics(vendor):
    """
    Computes all analytics data for a specific vendor.
    """
    now = timezone.now()
    today = now.date()

    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    last_30_days = today - timedelta(days=29)

    orders = Order.objects.filter(vendor=vendor).select_related("student")

    # Revenue
    today_revenue = (
        orders.filter(
            created_at__date=today,
            status=OrderStatus.COMPLETED
        ).aggregate(total=Sum("total_amount"))["total"] or 0
    )

    weekly_revenue = (
        orders.filter(
            created_at__date__gte=week_start,
            status=OrderStatus.COMPLETED
        ).aggregate(total=Sum("total_amount"))["total"] or 0
    )

    monthly_revenue = (
        orders.filter(
            created_at__date__gte=month_start,
            status=OrderStatus.COMPLETED
        ).aggregate(total=Sum("total_amount"))["total"] or 0
    )

    lifetime_revenue = (
        orders.filter(status=OrderStatus.COMPLETED)
        .aggregate(total=Sum("total_amount"))["total"] or 0
    )

    # Orders
    today_orders = orders.filter(created_at__date=today).count()
    weekly_orders = orders.filter(created_at__date__gte=week_start).count()
    monthly_orders = orders.filter(created_at__date__gte=month_start).count()
    total_orders = orders.count()

    # Status Counts
    pending_orders = orders.filter(status=OrderStatus.RECEIVED).count()
    accepted_orders = orders.filter(status=OrderStatus.ACCEPTED).count()
    preparing_orders = orders.filter(status=OrderStatus.PREPARING).count()
    ready_orders = orders.filter(status=OrderStatus.READY).count()
    completed_orders = orders.filter(status=OrderStatus.COMPLETED).count()
    cancelled_orders = orders.filter(status=OrderStatus.CANCELLED).count()
    rejected_orders = orders.filter(status=OrderStatus.REJECTED).count()

    # Average Order Value
    average_order_value = 0
    if completed_orders:
        average_order_value = lifetime_revenue / completed_orders

    # Revenue Chart (Last 30 Days)
    revenue_chart = (
        orders.filter(
            created_at__date__gte=last_30_days,
            status=OrderStatus.COMPLETED
        )
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(revenue=Sum("total_amount"))
        .order_by("day")
    )

    # Orders Per Day
    order_chart = (
        orders.filter(created_at__date__gte=last_30_days)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )

    # Top Selling Menu Items
    top_items = (
        OrderItem.objects.filter(
            order__vendor=vendor,
            order__status=OrderStatus.COMPLETED,
        )
        .values("menu_item__name")
        .annotate(
            quantity_sold=Sum("quantity"),
            revenue=Sum("subtotal"),
        )
        .order_by("-quantity_sold")[:5]
    )

    # Peak Ordering Hour
    peak_hour = (
        orders.annotate(hour=ExtractHour("created_at"))
        .values("hour")
        .annotate(total=Count("id"))
        .order_by("-total")
        .first()
    )

    # Completion & Cancellation Rates
    completion_rate = 0
    cancellation_rate = 0
    if total_orders:
        completion_rate = round((completed_orders / total_orders) * 100, 1)
        cancellation_rate = round((cancelled_orders / total_orders) * 100, 1)

    # Revenue Growth
    previous_week_start = week_start - timedelta(days=7)
    previous_week_end = week_start

    previous_week_revenue = (
        orders.filter(
            created_at__date__gte=previous_week_start,
            created_at__date__lt=previous_week_end,
            status=OrderStatus.COMPLETED,
        ).aggregate(total=Sum("total_amount"))["total"] or 0
    )

    revenue_growth = 0
    if previous_week_revenue:
        revenue_growth = round(
            ((weekly_revenue - previous_week_revenue) / previous_week_revenue) * 100,
            1
        )

    # Recent Orders
    recent_orders = orders.order_by("-created_at")[:10]

    return {
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
