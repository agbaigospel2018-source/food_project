from datetime import time
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from menu.models import MenuItem
from vendors.models import Vendor

from .models import Order


class OrderDetailAccessTests(TestCase):
    def setUp(self):
        self.student = get_user_model().objects.create_user(
            username="student",
            email="student@example.com",
            password="password123",
        )
        self.vendor_owner = get_user_model().objects.create_user(
            username="vendorowner",
            email="vendorowner@example.com",
            password="password123",
        )
        self.vendor = Vendor.objects.create(
            owner=self.vendor_owner,
            business_name="Bella Bistro",
            description="Fresh meals.",
            location="Downtown",
            phone_number="1234567890",
            opening_time=time(9, 0),
            closing_time=time(21, 0),
        )
        self.menu_item = MenuItem.objects.create(
            vendor=self.vendor,
            name="Burger",
            slug="burger",
            base_price="10.00",
        )
        self.order = Order.objects.create(
            student=self.student,
            vendor=self.vendor,
            pickup_time=timezone.now() + timezone.timedelta(hours=1),
            total_amount="10.00",
        )

    def test_vendor_owner_can_view_their_order_detail(self):
        self.client.force_login(self.vendor_owner)
        response = self.client.get(reverse("orders:order_detail", kwargs={"order_id": self.order.id}))

        self.assertEqual(response.status_code, 200)
