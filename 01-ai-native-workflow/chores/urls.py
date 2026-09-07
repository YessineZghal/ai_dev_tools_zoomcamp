from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("household/", views.household_detail, name="household_detail"),
    path("household/setup/", views.household_setup, name="household_setup"),
    path("mine/", views.my_chores, name="my_chores"),
    # Chores CRUD (Feature 1)
    path("chores/", views.chore_list, name="chore_list"),
    path("chores/new/", views.chore_create, name="chore_create"),
    path("chores/<int:pk>/edit/", views.chore_update, name="chore_update"),
    path("chores/<int:pk>/delete/", views.chore_delete, name="chore_delete"),
    # Assignments (Feature 2)
    path("chores/<int:pk>/assign/", views.assignment_create, name="assignment_create"),
    path(
        "assignments/<int:pk>/complete/",
        views.assignment_complete,
        name="assignment_complete",
    ),
    path("assignments/<int:pk>/skip/", views.assignment_skip, name="assignment_skip"),
    # Completion log (Feature 3)
    path("history/", views.history, name="history"),
]
