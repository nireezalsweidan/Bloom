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