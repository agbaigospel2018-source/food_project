from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from orders.models import Order, OrderStatus
from .models import Vendor


class VendorSearchSuggestionsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="vendorowner2",
            email="owner2@example.com",
            password="password123",
        )
        self.vendor = Vendor.objects.create(
            owner=self.user,
            business_name="Sunset Grill",
            description="Fresh comfort food.",
            location="North Campus",
            phone_number="1234567890",
            opening_time=time(8, 0),
            closing_time=time(20, 0),
        )

    def test_vendor_suggestions_return_matching_restaurants(self):
        response = self.client.get(reverse("vendors:vendor_search_suggestions"), {"q": "sunset"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("suggestions", payload)
        labels = [item["label"] for item in payload["suggestions"]]
        self.assertIn("Sunset Grill", labels)


class VendorDashboardOrderStatsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="vendorowner3",
            email="owner3@example.com",
            password="password123",
            role="vendor",
        )
        self.vendor = Vendor.objects.create(
            owner=self.user,
            business_name="Harbor Kitchen",
            description="Fresh comfort food.",
            location="West Campus",
            phone_number="1234567890",
            opening_time=time(8, 0),
            closing_time=time(20, 0),
        )
        self.student = get_user_model().objects.create_user(
            username="student3",
            email="student3@example.com",
            password="password123",
            role="student",
        )

    def test_dashboard_counts_and_lists_vendor_orders(self):
        Order.objects.create(
            student=self.student,
            vendor=self.vendor,
            pickup_time=timezone.now() + timedelta(hours=1),
            status=OrderStatus.PENDING,
            total_amount="15.00",
        )
        Order.objects.create(
            student=self.student,
            vendor=self.vendor,
            pickup_time=timezone.now() + timedelta(hours=2),
            status=OrderStatus.ACCEPTED,
            total_amount="20.00",
        )
        Order.objects.create(
            student=self.student,
            vendor=self.vendor,
            pickup_time=timezone.now() + timedelta(hours=3),
            status=OrderStatus.COMPLETED,
            total_amount="30.00",
        )

        self.client.force_login(self.user)

        dashboard_response = self.client.get(reverse("vendors:vendor_dashboard"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, "2")
        self.assertContains(dashboard_response, "1")
        self.assertContains(dashboard_response, "3")
        self.assertContains(dashboard_response, "Harbor Kitchen")

        orders_response = self.client.get(reverse("orders:vendor_orders"))
        self.assertEqual(orders_response.status_code, 200)
        self.assertContains(orders_response, "Pending")
        self.assertContains(orders_response, "Accepted")
        self.assertContains(orders_response, "Completed")
