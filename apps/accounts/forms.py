"""Forms for the accounts app."""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistrationForm(UserCreationForm):
    """User registration form with email field."""

    email = forms.EmailField(
        required=True,
        help_text="Required. Enter a valid email address.",
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def save(self, commit: bool = True) -> User:
        """Save the user with email."""
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
