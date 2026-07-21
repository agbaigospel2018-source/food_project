from django import forms

from .models import Category, MenuItem, MenuItemOptionGroup, MenuItemReview


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "sort_order", "is_active"]


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = [
            "category",
            "name",
            "description",
            "image",
            "base_price",
            "discount_price",
            "prep_time_minutes",
            "calories",
            "is_vegetarian",
            "is_vegan",
            "is_halal",
            "is_spicy",
            "is_featured",
            "is_active",
            "is_available",
            "stock_quantity",
            "available_from",
            "available_until",
            "sort_order",
        ]
        widgets = {
            "available_from": forms.TimeInput(attrs={"type": "time"}),
            "available_until": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, vendor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if vendor is not None:
            self.fields["category"].queryset = Category.objects.filter(vendor=vendor)


class MenuItemOptionGroupForm(forms.ModelForm):
    class Meta:
        model = MenuItemOptionGroup
        fields = ["name", "choice_type", "is_required", "min_choices", "max_choices", "sort_order"]


class ReviewForm(forms.ModelForm):
    class Meta:
        model = MenuItemReview
        fields = ["rating", "title", "comment"]
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5}),
        }
