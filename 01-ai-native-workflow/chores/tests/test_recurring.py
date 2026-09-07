from datetime import date, timedelta
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from chores.models import (
    Assignment,
    Chore,
    Household,
    Membership,
    _add_one_month,
)


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


class AddOneMonthTests(TestCase):
    def test_plain_month(self):
        self.assertEqual(_add_one_month(date(2026, 3, 15)), date(2026, 4, 15))

    def test_year_rollover(self):
        self.assertEqual(_add_one_month(date(2026, 12, 10)), date(2027, 1, 10))

    def test_clamps_to_short_month(self):
        self.assertEqual(_add_one_month(date(2026, 1, 31)), date(2026, 2, 28))

    def test_clamps_to_leap_february(self):
        self.assertEqual(_add_one_month(date(2024, 1, 31)), date(2024, 2, 29))


class NextDueTests(TestCase):
    def setUp(self):
        self.hh, self.ana = make_household("Flat A", "ana")

    def _chore(self, recurrence):
        return Chore.objects.create(
            household=self.hh, title="C", recurrence=recurrence
        )

    def test_intervals(self):
        base = date(2026, 6, 1)
        self.assertEqual(self._chore(Chore.Recurrence.DAILY).next_due(base), date(2026, 6, 2))
        self.assertEqual(self._chore(Chore.Recurrence.WEEKLY).next_due(base), date(2026, 6, 8))
        self.assertEqual(self._chore(Chore.Recurrence.BIWEEKLY).next_due(base), date(2026, 6, 15))
        self.assertEqual(self._chore(Chore.Recurrence.MONTHLY).next_due(base), date(2026, 7, 1))

    def test_is_recurring(self):
        self.assertFalse(self._chore(Chore.Recurrence.NONE).is_recurring)
        self.assertTrue(self._chore(Chore.Recurrence.WEEKLY).is_recurring)


class SpawnNextTests(TestCase):
    def setUp(self):
        self.hh, self.ana, self.bea, self.cy = make_household(
            "Flat A", "ana", "bea", "cy"
        )

    def _assignment(self, chore, assignee, due):
        return Assignment.objects.create(chore=chore, assignee=assignee, due_date=due)

    def test_completing_weekly_spawns_one_next_same_assignee(self):
        chore = Chore.objects.create(
            household=self.hh, title="Vacuum", recurrence=Chore.Recurrence.WEEKLY
        )
        due = date.today() - timedelta(days=1)
        a = self._assignment(chore, self.ana, due)
        a.complete(self.ana)

        nxt = chore.assignments.filter(status=Assignment.Status.PENDING).get()
        self.assertEqual(nxt.assignee, self.ana)
        self.assertEqual(nxt.due_date, max(due + timedelta(days=7), date.today()))

    def test_rotate_assignee_hands_to_next_member(self):
        chore = Chore.objects.create(
            household=self.hh,
            title="Trash",
            recurrence=Chore.Recurrence.DAILY,
            rotate_assignee=True,
        )
        a = self._assignment(chore, self.ana, date.today())
        a.complete(self.ana)
        nxt = chore.assignments.filter(status=Assignment.Status.PENDING).get()
        self.assertEqual(nxt.assignee, self.bea)  # ana -> bea (username order)

    def test_completing_twice_spawns_only_one(self):
        chore = Chore.objects.create(
            household=self.hh, title="Dishes", recurrence=Chore.Recurrence.DAILY
        )
        a = self._assignment(chore, self.ana, date.today())
        a.complete(self.ana)
        a.complete(self.ana)
        self.assertEqual(
            chore.assignments.filter(status=Assignment.Status.PENDING).count(), 1
        )

    def test_skipping_recurring_also_spawns_next(self):
        chore = Chore.objects.create(
            household=self.hh, title="Mop", recurrence=Chore.Recurrence.WEEKLY
        )
        a = self._assignment(chore, self.ana, date.today())
        a.skip()
        self.assertEqual(
            chore.assignments.filter(status=Assignment.Status.PENDING).count(), 1
        )

    def test_non_recurring_spawns_nothing(self):
        chore = Chore.objects.create(household=self.hh, title="One-off")
        a = self._assignment(chore, self.ana, date.today())
        a.complete(self.ana)
        self.assertEqual(chore.assignments.count(), 1)

    def test_inactive_recurring_spawns_nothing(self):
        chore = Chore.objects.create(
            household=self.hh,
            title="Paused",
            recurrence=Chore.Recurrence.DAILY,
            is_active=False,
        )
        a = self._assignment(chore, self.ana, date.today())
        a.complete(self.ana)
        self.assertEqual(
            chore.assignments.filter(status=Assignment.Status.PENDING).count(), 0
        )

    def test_does_not_spawn_when_a_pending_one_already_exists(self):
        chore = Chore.objects.create(
            household=self.hh, title="Busy", recurrence=Chore.Recurrence.DAILY
        )
        self._assignment(chore, self.bea, date.today() + timedelta(days=1))
        a = self._assignment(chore, self.ana, date.today())
        a.complete(self.ana)
        self.assertEqual(
            chore.assignments.filter(status=Assignment.Status.PENDING).count(), 1
        )


class GenerateRecurringCommandTests(TestCase):
    def setUp(self):
        self.hh, self.ana = make_household("Flat A", "ana")

    def test_creates_missing_occurrence_and_is_idempotent(self):
        chore = Chore.objects.create(
            household=self.hh, title="Bins", recurrence=Chore.Recurrence.WEEKLY
        )
        old = Assignment.objects.create(
            chore=chore, assignee=self.ana, due_date=date.today() - timedelta(days=10)
        )
        old.status = Assignment.Status.DONE
        old.save(update_fields=["status"])

        out = StringIO()
        call_command("generate_recurring", stdout=out)
        self.assertEqual(
            chore.assignments.filter(status=Assignment.Status.PENDING).count(), 1
        )

        call_command("generate_recurring", stdout=out)  # no-op second run
        self.assertEqual(
            chore.assignments.filter(status=Assignment.Status.PENDING).count(), 1
        )

    def test_ignores_non_recurring_and_inactive(self):
        Chore.objects.create(household=self.hh, title="One-off")
        Chore.objects.create(
            household=self.hh,
            title="Paused",
            recurrence=Chore.Recurrence.DAILY,
            is_active=False,
        )
        call_command("generate_recurring", stdout=StringIO())
        self.assertEqual(Assignment.objects.count(), 0)
