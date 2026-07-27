from datetime import time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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
