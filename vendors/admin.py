from django.contrib import admin
from django.utils.html import format_html

from .models import Vendor


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):

    list_display = (
        "logo_preview",
        "business_name",
        "owner",
        "status_badge",
        "location",
        "phone_number",
        "business_hours",
        "created_at",
    )

    list_filter = (
        "is_open",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "business_name",
        "owner__username",
        "owner__first_name",
        "owner__last_name",
        "owner__email",
        "location",
        "phone_number",
    )

    readonly_fields = (
        "logo_preview_large",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 20

    actions = (
        "open_vendors",
        "close_vendors",
    )

    fieldsets = (

        (
            "Vendor Information",
            {
                "fields": (
                    "owner",
                    "business_name",
                    "description",
                )
            },
        ),

        (
            "Branding",
            {
                "fields": (
                    "logo",
                    "logo_preview_large",
                )
            },
        ),

        (
            "Business Details",
            {
                "fields": (
                    "location",
                    "phone_number",
                    "opening_time",
                    "closing_time",
                    "is_open",
                )
            },
        ),

        (
            "System Information",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),

    )

    # ----------------------------
    # Logo Preview
    # ----------------------------

    @admin.display(description="Logo")
    def logo_preview(self, obj):

        if obj.logo:
            return format_html(
                '<img src="{}" width="45" height="45" '
                'style="border-radius:8px;object-fit:cover;">',
                obj.logo.url
            )

        return "-"

    @admin.display(description="Current Logo")
    def logo_preview_large(self, obj):

        if obj.logo:
            return format_html(
                '<img src="{}" width="180" '
                'style="border-radius:10px;">',
                obj.logo.url
            )

        return "No logo uploaded."

    # ----------------------------
    # Status Badge
    # ----------------------------

    @admin.display(description="Status")
    def status_badge(self, obj):

        if obj.is_open:
            color = "#16a34a"
            text = "Open"
        else:
            color = "#dc2626"
            text = "Closed"

        return format_html(
            '<span style="'
            'background:{};'
            'color:white;'
            'padding:4px 10px;'
            'border-radius:20px;'
            'font-size:12px;'
            'font-weight:bold;">'
            '{}'
            '</span>',
            color,
            text,
        )

    # ----------------------------
    # Business Hours
    # ----------------------------

    @admin.display(description="Business Hours")
    def business_hours(self, obj):
        return f"{obj.opening_time} - {obj.closing_time}"

    # ----------------------------
    # Bulk Actions
    # ----------------------------

    @admin.action(description="Mark selected vendors as Open")
    def open_vendors(self, request, queryset):

        updated = queryset.update(is_open=True)

        self.message_user(
            request,
            f"{updated} vendor(s) marked as Open."
        )

    @admin.action(description="Mark selected vendors as Closed")
    def close_vendors(self, request, queryset):

        updated = queryset.update(is_open=False)

        self.message_user(
            request,
            f"{updated} vendor(s) marked as Closed."
        )