from django import forms

from .models import CartItem, Category, MenuItem, MenuItemOptionGroup, MenuItemReview


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


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=99, initial=1)
    note = forms.CharField(max_length=255, required=False)
    options = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, menu_item=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.menu_item = menu_item
        if menu_item is None:
            self.fields["options"].choices = []
            return
        choices = []
        for group in menu_item.option_groups.prefetch_related("options"):
            for option in group.options.filter(is_available=True):
                label = f"{group.name}: {option.name}"
                if option.price_delta:
                    label = f"{label} (+{option.price_delta})"
                choices.append((str(option.id), label))
        self.fields["options"].choices = choices


class CartItemUpdateForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ["quantity", "note"]


class ReviewForm(forms.ModelForm):
    class Meta:
        model = MenuItemReview
        fields = ["rating", "title", "comment"]
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5}),
        }
