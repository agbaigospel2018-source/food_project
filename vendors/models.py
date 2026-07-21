from django.db import models
from django.conf import settings
# Create your models here.

class Vendor(models.Model):

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_profile'
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
        default=True
    )

    logo = models.ImageField(
        upload_to='vendors/logos/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.business_name

