from django import forms
from .models import Vendor


class VendorForm(forms.ModelForm):

    class Meta:

        model = Vendor

        fields = (
            'business_name',
            'description',
            'location',
            'phone_number',
            'opening_time',
            'closing_time',
            'logo',
        )