
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterForm(UserCreationForm):

    # pyrefly: ignore [bad-override]
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'phone_number',
            'role',
            'password1',
            'password2',
            'profile_image',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-orange-500'
            })

        
        
class ProfileUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'phone_number',
            'profile_image',
        )
    
    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
    
            for field in self.fields.values():
                field.widget.attrs.update({
                    'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-orange-500'
                })
                

