from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from .forms import RegistrationForm


class RegisterView(View):
    template_name: str = "accounts/register.html"

    def get(self, request: HttpRequest) -> HttpResponse | HttpResponseRedirect:
        if request.user.is_authenticated:
            return redirect("stories:home")
        form = RegistrationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse | HttpResponseRedirect:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("stories:home")
        return render(request, self.template_name, {"form": form})


class CustomLoginView(LoginView):
    template_name: str = "accounts/login.html"
    redirect_authenticated_user: bool = True

    def get_success_url(self) -> str:
        return str(reverse_lazy("stories:home"))


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")
