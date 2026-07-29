from django import forms
from .models import Vendor


class VendorForm(forms.ModelForm):

    class Meta:
        model = Vendor

        fields = (
            "business_name",
            "description",
            "location",
            "phone_number",
            "opening_time",
            "closing_time",
            "logo",
        )

        widgets = {
            "business_name": forms.TextInput(attrs={
                "class": "w-full rounded-xl border-gray-300 focus:border-orange-500 focus:ring-orange-500"
            }),
            "description": forms.Textarea(attrs={
                "rows": 5,
                "class": "w-full rounded-xl border-gray-300 focus:border-orange-500 focus:ring-orange-500"
            }),
            "location": forms.TextInput(attrs={
                "class": "w-full rounded-xl border-gray-300 focus:border-orange-500 focus:ring-orange-500"
            }),
            "phone_number": forms.TextInput(attrs={
                "class": "w-full rounded-xl border-gray-300 focus:border-orange-500 focus:ring-orange-500"
            }),
            "opening_time": forms.TimeInput(attrs={
                "type": "time",
                "class": "w-full rounded-xl border-gray-300 focus:border-orange-500 focus:ring-orange-500"
            }),
            "closing_time": forms.TimeInput(attrs={
                "type": "time",
                "class": "w-full rounded-xl border-gray-300 focus:border-orange-500 focus:ring-orange-500"
            }),
            "logo": forms.ClearableFileInput(attrs={
                "class": "block w-full text-sm"
            }),
        }
        

class BusinessHoursForm(forms.ModelForm):

    class Meta:

        model = Vendor

        fields = (
            "opening_time",
            "closing_time",
        )

        widgets = {

            "opening_time": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "w-full rounded-xl border-gray-300 focus:border-orange-500 focus:ring-orange-500"
                }
            ),

            "closing_time": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "w-full rounded-xl border-gray-300 focus:border-orange-500 focus:ring-orange-500"
                }
            ),

        }