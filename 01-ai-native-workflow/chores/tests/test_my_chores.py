from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from chores.context_processors import overdue_badge
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


class MyChoresPageTests(TestCase):
    def setUp(self):
        self.hh, self.ana, self.bea = make_household("Flat A", "ana", "bea")
        self.chore = Chore.objects.create(household=self.hh, title="Dishes")
        self.client.login(username="ana", password="chore-pass-123")

    def _mk(self, assignee, status=Assignment.Status.PENDING, days=0):
        a = Assignment.objects.create(
            chore=self.chore,
            assignee=assignee,
            due_date=date.today() + timedelta(days=days),
        )
        if status != Assignment.Status.PENDING:
            a.status = status
            a.save(update_fields=["status"])
        return a

    def test_default_shows_only_my_pending(self):
        mine_pending = self._mk(self.ana)
        self._mk(self.ana, Assignment.Status.DONE)
        self._mk(self.bea)  # someone else's

        response = self.client.get(reverse("my_chores"))
        pks = [a.pk for a in response.context["assignments"]]
        self.assertEqual(pks, [mine_pending.pk])

    def test_status_all_shows_all_of_mine_only(self):
        self._mk(self.ana)
        self._mk(self.ana, Assignment.Status.DONE)
        self._mk(self.bea)

        response = self.client.get(reverse("my_chores"), {"status": "all"})
        assignees = {a.assignee_id for a in response.context["assignments"]}
        self.assertEqual(assignees, {self.ana.pk})
        self.assertEqual(len(response.context["assignments"]), 2)

    def test_status_done_filters(self):
        self._mk(self.ana)
        done = self._mk(self.ana, Assignment.Status.DONE)
        response = self.client.get(reverse("my_chores"), {"status": "done"})
        self.assertEqual([a.pk for a in response.context["assignments"]], [done.pk])

    def test_bad_status_falls_back_to_pending(self):
        pending = self._mk(self.ana)
        self._mk(self.ana, Assignment.Status.SKIPPED)
        response = self.client.get(reverse("my_chores"), {"status": "bogus"})
        self.assertEqual([a.pk for a in response.context["assignments"]], [pending.pk])

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("my_chores"))
        self.assertEqual(response.status_code, 302)


class OverdueBadgeContextProcessorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.hh, self.ana = make_household("Flat A", "ana")
        self.chore = Chore.objects.create(household=self.hh, title="Dishes")

    def _request_as(self, user):
        request = self.factory.get("/")
        request.user = user
        return request

    def test_counts_my_overdue_pending(self):
        Assignment.objects.create(
            chore=self.chore, assignee=self.ana,
            due_date=date.today() - timedelta(days=1),
        )
        Assignment.objects.create(
            chore=self.chore, assignee=self.ana, due_date=date.today(),
        )  # not overdue
        result = overdue_badge(self._request_as(self.ana))
        self.assertEqual(result, {"nav_overdue_count": 1})

    def test_empty_for_anonymous(self):
        from django.contrib.auth.models import AnonymousUser

        self.assertEqual(overdue_badge(self._request_as(AnonymousUser())), {})

    def test_empty_for_user_without_household(self):
        loner = User.objects.create_user("loner", password="x")
        self.assertEqual(overdue_badge(self._request_as(loner)), {})
