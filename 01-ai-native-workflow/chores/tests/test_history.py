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


class HistoryTests(TestCase):
    def setUp(self):
        self.hh_a, self.ana = make_household("Flat A", "ana")
        self.bea = User.objects.create_user("bea", password="chore-pass-123")
        Membership.objects.create(user=self.bea, household=self.hh_a, display_name="bea")
        self.hh_b, self.zed = make_household("Flat B", "zed")
        self.client.login(username="ana", password="chore-pass-123")

    def _complete(self, household, actor, title):
        chore = Chore.objects.create(household=household, title=title, points=2)
        assignment = Assignment.objects.create(
            chore=chore, assignee=actor, due_date=date.today()
        )
        return assignment.complete(actor)

    def test_history_lists_household_events_newest_first(self):
        first = self._complete(self.hh_a, self.ana, "Dishes")
        second = self._complete(self.hh_a, self.bea, "Trash")
        response = self.client.get(reverse("history"))
        events = list(response.context["events"])
        self.assertEqual([e.pk for e in events], [second.pk, first.pk])

    def test_history_excludes_other_household(self):
        self._complete(self.hh_a, self.ana, "Dishes")
        self._complete(self.hh_b, self.zed, "SecretB")
        response = self.client.get(reverse("history"))
        self.assertContains(response, "Dishes")
        self.assertNotContains(response, "SecretB")

    def test_history_member_filter(self):
        self._complete(self.hh_a, self.ana, "AnaChore")
        self._complete(self.hh_a, self.bea, "BeaChore")
        response = self.client.get(reverse("history"), {"member": self.bea.pk})
        titles = [e.assignment.chore.title for e in response.context["events"]]
        self.assertEqual(titles, ["BeaChore"])

    def test_history_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("history"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])
