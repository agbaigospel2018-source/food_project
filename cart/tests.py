from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from cart.context_processors import cart_count
from cart.models import Cart, CartItem
from menu.models import MenuItem
from vendors.models import Vendor


class CartContextProcessorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.student_user = get_user_model().objects.create_user(
            username="student1",
            password="testpass123",
            role="student",
        )
        self.vendor_user = get_user_model().objects.create_user(
            username="vendor1",
            password="testpass123",
            role="vendor",
        )
        # pyrefly: ignore [missing-attribute]
        self.vendor = Vendor.objects.create(
            owner=self.vendor_user,
            business_name="Test Vendor",
            description="A test vendor",
            location="Downtown",
            phone_number="1234567890",
            opening_time="09:00:00",
            closing_time="21:00:00",
        )

    def test_cart_count_context_processor_returns_total_quantity(self):
        first_item = MenuItem.objects.create(
            vendor=self.vendor,
            name="Burger",
            slug="burger",
            base_price="10.00",
        )
        second_item = MenuItem.objects.create(
            vendor=self.vendor,
            name="Fries",
            slug="fries",
            base_price="5.00",
        )
        # pyrefly: ignore [missing-attribute]
        cart = Cart.objects.create(student=self.student_user)
        # pyrefly: ignore [missing-attribute]
        CartItem.objects.create(cart=cart, menu_item=first_item, quantity=2)
        # pyrefly: ignore [missing-attribute]
        CartItem.objects.create(cart=cart, menu_item=second_item, quantity=1)

        request = self.factory.get("/")
        # pyrefly: ignore [missing-attribute]
        request.user = self.student_user

        self.assertEqual(cart_count(request)["cart_count"], 3)
