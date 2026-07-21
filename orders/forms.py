from django import forms

from .models import Order, OrderItem


class OrderForm(forms.ModelForm):

    class Meta:
        model = Order

        fields = [
            "pickup_time",
        ]

        widgets = {
            "pickup_time": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "w-full rounded-lg border border-gray-300 p-3 focus:ring-2 focus:ring-orange-500",
                }
            ),
        }


class OrderItemForm(forms.ModelForm):

    class Meta:
        model = OrderItem

        fields = [
            "menu_item",
            "quantity",
        ]

        widgets = {
            "menu_item": forms.Select(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 p-3 focus:ring-2 focus:ring-orange-500",
                }
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "min": 1,
                    "class": "w-full rounded-lg border border-gray-300 p-3 focus:ring-2 focus:ring-orange-500",
                }
            ),
        }