from django.contrib import admin
from .models import Order, OrderItem

# Register your models here.
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = (
        'short_id',
        'student',
        'vendor',
        'status',
        'pickup_time',
        'total_amount',
        'created_at',
    )
    
    list_filter = (
        'status',
        'vendor',
        'created_at',
    )
    
    search_fields = (
        'student__username',
        'vendor__business_name',
    )
    
    ordering = (
        '-created_at',
    )
    
    # pyrefly: ignore [bad-override-mutable-attribute]
    inlines = [
        OrderItemInline,
    ]
    
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = (
        'order',
        'menu_item',
        'quantity',
        'unit_price',
        'subtotal',
        'created_at',
    )
    
    search_fields = (
        'order__id',
        'menu_item__name',
    )
    
    list_filter = (
        'menu_item',
    )
    
