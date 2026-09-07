"""URL configuration for the household project."""

from django.contrib import admin
from django.urls import include, path

from chores import views as chore_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/register/", chore_views.register, name="register"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("chores.urls")),
]
