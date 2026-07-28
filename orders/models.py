import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from vendors.models import Vendor
from menu.models import MenuItem


# ==========================================
# Order Status
# ==========================================

class OrderStatus(models.TextChoices):
    RECEIVED = "received", "Order Received"
    ACCEPTED = "accepted", "Accepted"
    PREPARING = "preparing", "Preparing"
    READY = "ready", "Ready for Pickup"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    REJECTED = "rejected", "Rejected"


# ==========================================
# Payment Status
# ==========================================

class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    REFUNDED = "refunded", "Refunded"


# ==========================================
# Order
# ==========================================

class Order(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.RECEIVED
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )

    pickup_time = models.DateTimeField()

    estimated_ready_time = models.DateTimeField(
        blank=True,
        null=True
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    vendor_note = models.TextField(
        blank=True
    )

    cancellation_reason = models.TextField(
        blank=True
    )

    # Timeline

    accepted_at = models.DateTimeField(
        blank=True,
        null=True
    )

    preparing_at = models.DateTimeField(
        blank=True,
        null=True
    )

    ready_at = models.DateTimeField(
        blank=True,
        null=True
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    cancelled_at = models.DateTimeField(
        blank=True,
        null=True
    )

    rejected_at = models.DateTimeField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

        verbose_name = "Order"

        verbose_name_plural = "Orders"

        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["student"]),
            models.Index(fields=["vendor"]),
        ]

    def __str__(self):
        return f"Order #{self.short_id()}"

    def short_id(self):
        return str(self.id)[:8]

    short_id.short_description = "Order ID"

    # --------------------------------------

    def update_total_amount(self):

        total = sum(
            item.subtotal for item in self.items.all()
        )

        self.total_amount = total or Decimal("0.00")

        self.save(
            update_fields=["total_amount"]
        )

    # ======================================
    # Helper Properties
    # ======================================

    @property
    def is_active(self):
        return self.status not in [
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        ]

    @property
    def can_be_cancelled(self):
        return self.status in [
            OrderStatus.RECEIVED,
            OrderStatus.ACCEPTED,
        ]

    @property
    def can_be_accepted(self):
        return self.status == OrderStatus.RECEIVED

    @property
    def can_be_prepared(self):
        return self.status == OrderStatus.ACCEPTED

    @property
    def can_be_marked_ready(self):
        return self.status == OrderStatus.PREPARING

    @property
    def can_be_completed(self):
        return self.status == OrderStatus.READY

    # ======================================
    # Status Methods
    # ======================================

    def accept(self):

        self.status = OrderStatus.ACCEPTED

        self.accepted_at = timezone.now()

        self.save()

    def start_preparing(self):

        self.status = OrderStatus.PREPARING

        self.preparing_at = timezone.now()

        self.save()

    def mark_ready(self):

        self.status = OrderStatus.READY

        self.ready_at = timezone.now()

        self.save()

    def complete(self):

        self.status = OrderStatus.COMPLETED

        self.completed_at = timezone.now()

        self.save()

    def cancel(self, reason=""):

        self.status = OrderStatus.CANCELLED

        self.cancelled_at = timezone.now()

        self.cancellation_reason = reason

        self.save()

    def reject(self, reason=""):

        self.status = OrderStatus.REJECTED

        self.rejected_at = timezone.now()

        self.cancellation_reason = reason

        self.save()


# ==========================================
# Order Item
# ==========================================

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="order_items"
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["id"]

        verbose_name = "Order Item"

        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity} × {self.menu_item.name}"

    def save(self, *args, **kwargs):

        if not self.unit_price:
            self.unit_price = self.menu_item.current_price

        self.subtotal = self.quantity * self.unit_price

        super().save(*args, **kwargs)

        self.order.update_total_amount()

    def delete(self, *args, **kwargs):

        order = self.order

        super().delete(*args, **kwargs)

        order.update_total_amount()