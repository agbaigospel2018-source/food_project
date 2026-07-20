from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'phone_number',
            'role',
            'password1',
            'password2',
        )


class ProfileUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'phone_number',
        )