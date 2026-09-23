from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "phone_number"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CUSTOMER   # role is always forced here, never from POST data
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "phone_number", "delivery_address"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "w-full px-4 py-3 rounded-lg bg-surface-container-low text-on-surface font-body-md text-body-md focus:outline-none focus:ring-2 focus:ring-secondary"}),
            "phone_number": forms.TextInput(attrs={"class": "w-full px-4 py-3 rounded-lg bg-surface-container-low text-on-surface font-body-md text-body-md focus:outline-none focus:ring-2 focus:ring-secondary"}),
            "delivery_address": forms.TextInput(attrs={"class": "w-full px-4 py-3 rounded-lg bg-surface-container-low text-on-surface font-body-md text-body-md focus:outline-none focus:ring-2 focus:ring-secondary"}),
        }