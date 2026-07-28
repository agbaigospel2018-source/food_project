from datetime import datetime

from django.db import models
from django.conf import settings


class Vendor(models.Model):

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vendor_profile"
    )

    business_name = models.CharField(
        max_length=100
    )

    description = models.TextField()

    location = models.CharField(
        max_length=100
    )

    phone_number = models.CharField(
        max_length=15
    )

    opening_time = models.TimeField()

    closing_time = models.TimeField()

    is_open = models.BooleanField(
        default=True,
        help_text="Temporarily open or close your restaurant."
    )

    logo = models.ImageField(
        upload_to="vendors/logos/",
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
        ordering = ["business_name"]
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"

    def __str__(self):
        return self.business_name

    @property
    def is_currently_open(self):
        """
        Returns True if the vendor is marked open and
        the current time falls within operating hours.
        """

        if not self.is_open:
            return False

        now = datetime.now().time()

        # Handles overnight businesses
        if self.opening_time <= self.closing_time:
            return self.opening_time <= now <= self.closing_time

        return now >= self.opening_time or now <= self.closing_time

    @property
    def status(self):
        """
        Human-readable status.
        """

        return "Open Now" if self.is_currently_open else "Closed"

    @property
    def operating_hours(self):
        """
        Returns nicely formatted operating hours.
        Example:
        8:00 AM - 8:00 PM
        """

        return (
            f"{self.opening_time.strftime('%I:%M %p')} - "
            f"{self.closing_time.strftime('%I:%M %p')}"
        )

    @property
    def initials(self):
        """
        Returns business initials.

        Belleful Express -> BE
        Mama Kitchen -> MK
        """

        words = self.business_name.split()

        if len(words) == 1:
            return words[0][:2].upper()

        return "".join(
            word[0].upper()
            for word in words[:2]
        )

    @property
    def logo_or_initials(self):
        """
        Convenience helper for templates.
        """

        if self.logo:
            return self.logo.url

        return self.initials

    @property
    def business_status_color(self):
        """
        Tailwind color helper.
        """

        return (
            "green"
            if self.is_currently_open
            else "red"
        )

    @property
    def formatted_phone(self):
        """
        Placeholder for future phone formatting.
        """

        return self.phone_number

    @property
    def short_description(self):
        """
        Short description for cards.
        """

        if len(self.description) <= 120:
            return self.description

        return self.description[:120] + "..."

    @property
    def logo_exists(self):
        """
        True if a logo has been uploaded.
        """

        return bool(self.logo)
    
    @property
    def menu_count(self):
        return self.menu_items.filter(is_available=True).count()

    @property
    def total_orders(self):
        return self.orders.count()

    @property
    def pending_orders(self):
        return self.orders.filter(status="received").count()

    @property
    def completed_orders(self):
        return self.orders.filter(status="completed").count()
    
    @property
    def operating_hours(self):
        return f"{self.opening_time.strftime('%I:%M %p')} - {self.closing_time.strftime('%I:%M %p')}"

    @property
    def is_currently_open(self):
        from django.utils import timezone

        now = timezone.localtime().time()

        return (
            self.is_open and
            self.opening_time <= now <= self.closing_time
        )