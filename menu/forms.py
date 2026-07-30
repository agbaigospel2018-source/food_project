from django import forms

from .models import Category, Ingredient, IngredientCategory, MenuItem, MenuItemOptionGroup, MenuItemReview


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
            # pyrefly: ignore [missing-attribute]
            self.fields["category"].queryset = Category.objects.filter(is_active=True)
            self.fields["category"].empty_label = "Choose a category"


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


class IngredientCategoryForm(forms.ModelForm):
    class Meta:
        model = IngredientCategory
        fields = ["name", "max_selectable_items", "display_order"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Bases, Proteins, Toppings"}),
            "max_selectable_items": forms.NumberInput(attrs={"min": 1}),
            "display_order": forms.NumberInput(attrs={"min": 0}),
        }


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ["name", "category", "price", "image_url", "calories", "protein", "carbs", "fats"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Jollof Rice"}),
            "price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "image_url": forms.URLInput(attrs={"placeholder": "https://example.com/image.jpg"}),
            "calories": forms.NumberInput(attrs={"min": 0}),
            "protein": forms.NumberInput(attrs={"step": "0.1", "min": "0"}),
            "carbs": forms.NumberInput(attrs={"step": "0.1", "min": "0"}),
            "fats": forms.NumberInput(attrs={"step": "0.1", "min": "0"}),
        }

    def __init__(self, *args, vendor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if vendor is not None:
            # Only show categories belonging to this vendor
            self.fields["category"].queryset = IngredientCategory.objects.filter(vendor=vendor)
            self.fields["category"].empty_label = "Choose a category"
