import uuid

from django.conf import settings
from django.db import models
from decimal import Decimal

from vendors.models import Vendor
from menu.models import MenuItem

# Create your models here.
class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    ACCEPTED = 'accepted', 'Accepted'
    PREPARING = 'preparing', 'Preparing'
    READY = 'ready', 'Ready for Pickup'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
    REJECTED = 'rejected', 'Rejected'
    
    
class Order(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name="orders"
    )
    
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    
    pickup_time = models.DateTimeField()
    
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        
    def __str__(self):
        return f'Order{self.id}'
    
    def short_id(self):
        return str(self.id)[:8]
    
    short_id.short_description = 'Order ID'
    
    def update_total_amount(self):
        total = sum(
            item.subtotal for item in self.items.all()
        )
        
        self.total_amount = total or Decimal('0.00')
        self.save(udpate_fields=['total_amount'])
    
    
class OrderItem(models.Model):
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='orders_items'
    )
    
    quantity = models.PositiveIntegerField(
        default=1
    )
    
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    class Meta:
        ordering = ['id']
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        
    def __str__(self):
        return f'{self.quantity} x {self.menu_item.name}'
    
    def save(self, *args, **kwargs):
        
        if not self.unit_price:
            self.unit_price = self.menu_item.price
            
        self.subtotal = self.quantity * self.unit_price
        
        super().save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        order = self.order
        
        super().delete(*args, **kwargs)
        