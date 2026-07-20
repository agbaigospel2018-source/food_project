from django.contrib import admin
from .models import Vendor
# Register your models here.

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):

    list_display = (
        'business_name',
        'location',
        'is_open',
    )

    search_fields = (
        'business_name',
        'location',
    )

    list_filter = (
        'is_open',
    )