from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from chores.models import Assignment, Chore, Household, Membership


def make_household(name, *usernames):
    household = Household.objects.create(name=name)
    users = []
    for username in usernames:
        user = User.objects.create_user(username, password="chore-pass-123")
        Membership.objects.create(
            user=user, household=household, display_name=username
        )
        users.append(user)
    return (household, *users)


class HouseholdDetailTests(TestCase):
    def setUp(self):
        self.hh, self.ana, self.bea = make_household("Flat A", "ana", "bea")
        self.other_hh, self.zed = make_household("Flat B", "zed")
        self.client.login(username="ana", password="chore-pass-123")

    def test_lists_members_with_points_and_pending_counts(self):
        chore = Chore.objects.create(household=self.hh, title="Dishes", points=4)
        done = Assignment.objects.create(
            chore=chore, assignee=self.ana, due_date=date.today()
        )
        done.complete(self.ana)
        Assignment.objects.create(
            chore=chore, assignee=self.bea, due_date=date.today()
        )

        response = self.client.get(reverse("household_detail"))
        self.assertEqual(response.status_code, 200)
        rows = {r["membership"].user.username: r for r in response.context["members"]}
        self.assertEqual(rows["ana"]["points_30d"], 4)
        self.assertEqual(rows["ana"]["pending_count"], 0)
        self.assertEqual(rows["bea"]["points_30d"], 0)
        self.assertEqual(rows["bea"]["pending_count"], 1)

    def test_shows_invite_code(self):
        response = self.client.get(reverse("household_detail"))
        self.assertContains(response, self.hh.invite_code)

    def test_does_not_leak_other_household_members(self):
        response = self.client.get(reverse("household_detail"))
        usernames = {r["membership"].user.username for r in response.context["members"]}
        self.assertEqual(usernames, {"ana", "bea"})

    def test_post_updates_own_display_name(self):
        response = self.client.post(
            reverse("household_detail"), {"display_name": "Ana B."}
        )
        self.assertRedirects(response, reverse("household_detail"))
        self.ana.membership.refresh_from_db()
        self.assertEqual(self.ana.membership.display_name, "Ana B.")
        # bea untouched
        self.bea.membership.refresh_from_db()
        self.assertEqual(self.bea.membership.display_name, "bea")

    def test_display_name_appears_on_dashboard_leaderboard(self):
        self.ana.membership.display_name = "Ana the Great"
        self.ana.membership.save()
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Ana the Great")

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("household_detail"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])
