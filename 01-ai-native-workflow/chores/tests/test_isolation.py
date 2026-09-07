"""One place a reviewer can check that households never see each other's data.

Some assertions overlap with the per-feature test files on purpose: this file
is the single audit point for cross-household isolation.
"""

from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from chores.models import Assignment, Chore, Household, Membership


def make_household(name, username):
    household = Household.objects.create(name=name)
    user = User.objects.create_user(username, password="chore-pass-123")
    Membership.objects.create(user=user, household=household, display_name=username)
    return household, user


class CrossHouseholdIsolationTests(TestCase):
    def setUp(self):
        self.hh_a, self.ana = make_household("Flat A", "ana")
        self.hh_b, self.bo = make_household("Flat B", "bo")
        self.chore_b = Chore.objects.create(household=self.hh_b, title="B-chore", points=9)
        self.assignment_b = Assignment.objects.create(
            chore=self.chore_b, assignee=self.bo, due_date=date.today()
        )
        self.client.login(username="ana", password="chore-pass-123")

    def test_chore_list_hides_other_household(self):
        response = self.client.get(reverse("chore_list"))
        self.assertNotContains(response, "B-chore")

    def test_cannot_edit_other_household_chore(self):
        self.assertEqual(
            self.client.get(reverse("chore_update", args=[self.chore_b.pk])).status_code,
            404,
        )

    def test_cannot_delete_other_household_chore(self):
        self.assertEqual(
            self.client.post(reverse("chore_delete", args=[self.chore_b.pk])).status_code,
            404,
        )

    def test_cannot_assign_within_other_household_chore(self):
        self.assertEqual(
            self.client.get(
                reverse("assignment_create", args=[self.chore_b.pk])
            ).status_code,
            404,
        )

    def test_cannot_complete_other_household_assignment(self):
        response = self.client.post(
            reverse("assignment_complete", args=[self.assignment_b.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assignment_b.refresh_from_db()
        self.assertEqual(self.assignment_b.status, Assignment.Status.PENDING)

    def test_cannot_skip_other_household_assignment(self):
        self.assertEqual(
            self.client.post(
                reverse("assignment_skip", args=[self.assignment_b.pk])
            ).status_code,
            404,
        )

    def test_history_hides_other_household_events(self):
        self.assignment_b.complete(self.bo)
        response = self.client.get(reverse("history"))
        self.assertNotContains(response, "B-chore")

    def test_dashboard_hides_other_household(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(list(response.context["household_overdue"]), [])
        self.assertEqual(list(response.context["recent_activity"]), [])
