from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from chores.models import Assignment, Chore, CompletionEvent, Household, Membership


def make_household(name, username):
    household = Household.objects.create(name=name)
    user = User.objects.create_user(username, password="chore-pass-123")
    Membership.objects.create(user=user, household=household, display_name=username)
    return household, user


class DashboardTests(TestCase):
    def setUp(self):
        self.hh, self.ana = make_household("Flat A", "ana")
        self.bea = User.objects.create_user("bea", password="chore-pass-123")
        Membership.objects.create(user=self.bea, household=self.hh, display_name="bea")
        self.hh_b, self.zed = make_household("Flat B", "zed")
        self.client.login(username="ana", password="chore-pass-123")

    def _chore(self, title, points=1, household=None):
        return Chore.objects.create(
            household=household or self.hh, title=title, points=points
        )

    def test_my_pending_only_mine_and_pending(self):
        mine = Assignment.objects.create(
            chore=self._chore("Dishes"), assignee=self.ana, due_date=date.today()
        )
        Assignment.objects.create(
            chore=self._chore("Trash"), assignee=self.bea, due_date=date.today()
        )
        done = Assignment.objects.create(
            chore=self._chore("Floor"), assignee=self.ana, due_date=date.today()
        )
        done.complete(self.ana)

        response = self.client.get(reverse("dashboard"))
        my_pending = list(response.context["my_pending"])
        self.assertEqual([a.pk for a in my_pending], [mine.pk])

    def test_overdue_panel_lists_household_past_due_pending(self):
        yesterday = date.today() - timedelta(days=1)
        overdue = Assignment.objects.create(
            chore=self._chore("Dishes"), assignee=self.bea, due_date=yesterday
        )
        Assignment.objects.create(
            chore=self._chore("Trash"), assignee=self.ana, due_date=date.today()
        )
        response = self.client.get(reverse("dashboard"))
        overdue_pks = [a.pk for a in response.context["household_overdue"]]
        self.assertEqual(overdue_pks, [overdue.pk])

    def test_recent_activity_capped_at_10_and_scoped(self):
        for i in range(12):
            a = Assignment.objects.create(
                chore=self._chore(f"C{i}"), assignee=self.ana, due_date=date.today()
            )
            a.complete(self.ana)
        other = Assignment.objects.create(
            chore=self._chore("B-secret", household=self.hh_b),
            assignee=self.zed,
            due_date=date.today(),
        )
        other.complete(self.zed)

        response = self.client.get(reverse("dashboard"))
        recent = list(response.context["recent_activity"])
        self.assertEqual(len(recent), 10)
        titles = {e.assignment.chore.title for e in recent}
        self.assertNotIn("B-secret", titles)

    def test_leaderboard_sums_last_30_days_ranked_desc(self):
        # Ana: 5 points recent. Bea: 3 points recent + 100 points old (excluded).
        a1 = Assignment.objects.create(
            chore=self._chore("Big", points=5), assignee=self.ana, due_date=date.today()
        )
        a1.complete(self.ana)
        a2 = Assignment.objects.create(
            chore=self._chore("Small", points=3), assignee=self.bea, due_date=date.today()
        )
        a2.complete(self.bea)
        a3 = Assignment.objects.create(
            chore=self._chore("Ancient", points=100),
            assignee=self.bea,
            due_date=date.today(),
        )
        old_event = a3.complete(self.bea)
        CompletionEvent.objects.filter(pk=old_event.pk).update(
            completed_at=timezone.now() - timedelta(days=45)
        )

        response = self.client.get(reverse("dashboard"))
        board = response.context["leaderboard"]
        self.assertEqual(
            [(r["member"].username, r["points"]) for r in board],
            [("ana", 5), ("bea", 3)],
        )

    def test_leaderboard_includes_zero_score_members(self):
        response = self.client.get(reverse("dashboard"))
        board = response.context["leaderboard"]
        self.assertEqual({r["member"].username for r in board}, {"ana", "bea"})
        self.assertTrue(all(r["points"] == 0 for r in board))

    def test_dashboard_shows_invite_code(self):
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, self.hh.invite_code)

    def test_dashboard_scoped_to_own_household_only(self):
        Assignment.objects.create(
            chore=self._chore("B-only", household=self.hh_b),
            assignee=self.zed,
            due_date=date.today() - timedelta(days=3),
        )
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(list(response.context["household_overdue"]), [])
