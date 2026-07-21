from django.contrib import admin

from .models import Cart, CartItem

# Register your models here.
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = (
        'menu_item',
        'quantity',
        'created_at',
        'updated_at',
    )
    
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):

    list_display = (
        "short_id",
        "student",
        "total_items",
        "total_amount",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "student__username",
        "student__email",
    )

    list_filter = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-updated_at",
    )

    inlines = [CartItemInline]

    @admin.display(description="Cart ID")
    def short_id(self, obj):
        return str(obj.id)[:8]

    @admin.display(description="Total Items")
    def total_items(self, obj):
        return obj.total_items

    @admin.display(description="Total Amount")
    def total_amount(self, obj):
        return obj.total_amount


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):

    list_display = (
        "cart",
        'vendor',
        "menu_item",
        "quantity",
        "line_total",
        "created_at",
    )

    search_fields = (
        "menu_item__name",
        "cart__student__username",
    )

    list_filter = (
        "created_at",
    )

    autocomplete_fields = (
        "cart",
        "menu_item",
    )

    ordering = (
        "-created_at",
    )

    @admin.display(description="Line Total")
    def line_total(self, obj):
        return obj.line_total
    
    @admin.display(description='Vendor')
    def vendor(self, obj):
        return obj.menu_item.vendor