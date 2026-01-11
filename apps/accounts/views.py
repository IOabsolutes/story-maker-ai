"""Views for the accounts app."""

from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from .forms import RegistrationForm


class RegisterView(View):
    """User registration view."""

    template_name = "accounts/register.html"

    def get(self, request):
        """Display registration form."""
        if request.user.is_authenticated:
            return redirect("stories:home")
        form = RegistrationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        """Process registration form."""
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("stories:home")
        return render(request, self.template_name, {"form": form})


class CustomLoginView(LoginView):
    """Custom login view."""

    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        """Redirect to home after login."""
        return reverse_lazy("stories:home")


class CustomLogoutView(LogoutView):
    """Custom logout view."""

    next_page = reverse_lazy("accounts:login")
