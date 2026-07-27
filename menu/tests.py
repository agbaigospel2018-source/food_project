from datetime import time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from vendors.models import Vendor

from .models import Category, MenuItem


class SearchSuggestionsViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="vendorowner",
            email="owner@example.com",
            password="password123",
        )
        self.vendor = Vendor.objects.create(
            owner=self.user,
            business_name="Bella Bistro",
            description="A cozy place for fresh meals.",
            location="Downtown",
            phone_number="1234567890",
            opening_time=time(9, 0),
            closing_time=time(21, 0),
        )
        self.category = Category.objects.create(
            name="Pizza",
            slug="pizza",
        )
        self.item = MenuItem.objects.create(
            vendor=self.vendor,
            category=self.category,
            name="Chicken Pizza",
            slug="chicken-pizza",
            base_price=Decimal("12.50"),
        )

    def test_suggestions_include_matching_items_and_vendors(self):
        item_response = self.client.get(reverse("menu:search_suggestions"), {"q": "pizza"})
        self.assertEqual(item_response.status_code, 200)
        item_payload = item_response.json()
        self.assertIn("suggestions", item_payload)
        item_labels = [suggestion["label"] for suggestion in item_payload["suggestions"]]
        self.assertIn("Chicken Pizza", item_labels)

        vendor_response = self.client.get(reverse("menu:search_suggestions"), {"q": "bella"})
        self.assertEqual(vendor_response.status_code, 200)
        vendor_payload = vendor_response.json()
        vendor_labels = [suggestion["label"] for suggestion in vendor_payload["suggestions"]]
        self.assertIn("Bella Bistro", vendor_labels)


class CategorySharingTests(TestCase):
    def test_categories_can_be_reused_across_vendors(self):
        owner_one = get_user_model().objects.create_user(
            username="vendorowner1",
            email="owner1@example.com",
            password="password123",
        )
        owner_two = get_user_model().objects.create_user(
            username="vendorowner2",
            email="owner2@example.com",
            password="password123",
        )
        vendor_one = Vendor.objects.create(
            owner=owner_one,
            business_name="Bella Bistro",
            description="A cozy place for fresh meals.",
            location="Downtown",
            phone_number="1234567890",
            opening_time=time(9, 0),
            closing_time=time(21, 0),
        )
        vendor_two = Vendor.objects.create(
            owner=owner_two,
            business_name="Sunset Grill",
            description="Great for dinner.",
            location="Uptown",
            phone_number="0987654321",
            opening_time=time(10, 0),
            closing_time=time(22, 0),
        )

        category = Category.objects.create(name="Desserts", slug="desserts")

        item = MenuItem.objects.create(
            vendor=vendor_two,
            category=category,
            name="Chocolate Cake",
            slug="chocolate-cake",
            base_price=Decimal("5.00"),
        )

        self.assertEqual(item.category, category)
