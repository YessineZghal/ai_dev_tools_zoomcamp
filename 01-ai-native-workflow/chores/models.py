"""Domain models for Choreo — a shared household chores manager.

The object graph is:

    Household 1--* Membership *--1 User
    Household 1--* Chore 1--* Assignment *--1 User (assignee)
    Assignment 1--* CompletionEvent *--1 User (completed_by)
"""

import calendar
import secrets
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

# Uppercase letters and digits with visually ambiguous characters removed
# (no O/0, I/1) so invite codes are easy to read aloud and type.
INVITE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
INVITE_CODE_LENGTH = 6


def generate_invite_code() -> str:
    return "".join(secrets.choice(INVITE_ALPHABET) for _ in range(INVITE_CODE_LENGTH))


def household_of(user) -> "Household | None":
    """Return the household the user belongs to, or None if they have no membership."""
    membership = getattr(user, "membership", None)
    return membership.household if membership is not None else None


def _add_one_month(d: date) -> date:
    """One calendar month after ``d``, clamping the day to the target month's length."""
    year, month = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))


class Household(models.Model):
    """A group of people who share a home and its chores."""

    name = models.CharField(max_length=100)
    invite_code = models.CharField(max_length=INVITE_CODE_LENGTH, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = self._unique_invite_code()
        super().save(*args, **kwargs)

    @staticmethod
    def _unique_invite_code() -> str:
        code = generate_invite_code()
        while Household.objects.filter(invite_code=code).exists():
            code = generate_invite_code()
        return code

    @property
    def members(self):
        """Users linked to this household through a Membership."""
        return (
            User.objects.filter(membership__household=self)
            .select_related("membership")
            .order_by("username")
        )


class Membership(models.Model):
    """Links exactly one User to exactly one Household."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="membership"
    )
    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name="memberships"
    )
    display_name = models.CharField(max_length=100)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_name"]

    def __str__(self) -> str:
        return f"{self.display_name} @ {self.household.name}"


class Chore(models.Model):
    """A task the household cares about (the catalogue entry).

    A chore may be one-off (``recurrence == NONE``) or repeating. When a
    repeating chore's assignment is completed or skipped, the next occurrence is
    created automatically (see ``Assignment.spawn_next``).
    """

    class Recurrence(models.TextChoices):
        NONE = "NONE", "Does not repeat"
        DAILY = "DAILY", "Daily"
        WEEKLY = "WEEKLY", "Weekly"
        BIWEEKLY = "BIWEEKLY", "Every 2 weeks"
        MONTHLY = "MONTHLY", "Monthly"

    _INTERVAL_DAYS = {
        Recurrence.DAILY: 1,
        Recurrence.WEEKLY: 7,
        Recurrence.BIWEEKLY: 14,
    }

    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name="chores"
    )
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    points = models.PositiveIntegerField(
        default=1, help_text="Rough effort weight, used for the leaderboard."
    )
    is_active = models.BooleanField(default=True)
    recurrence = models.CharField(
        max_length=10, choices=Recurrence.choices, default=Recurrence.NONE
    )
    rotate_assignee = models.BooleanField(
        default=False,
        help_text="Pass each new occurrence to the next household member.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title

    @property
    def is_recurring(self) -> bool:
        return self.recurrence != self.Recurrence.NONE

    def next_due(self, after: date) -> date:
        """The due date of the occurrence that follows one due on ``after``."""
        if self.recurrence == self.Recurrence.MONTHLY:
            return _add_one_month(after)
        days = self._INTERVAL_DAYS.get(self.recurrence)
        if days is None:
            return after
        return after + timedelta(days=days)

    def next_assignee(self, current: User) -> User:
        """Who gets the next occurrence: ``current``, or the next member if rotating."""
        members = list(self.household.members)
        if not members:
            return current
        if not self.rotate_assignee:
            return current
        try:
            index = members.index(current)
        except ValueError:
            return members[0]
        return members[(index + 1) % len(members)]


class Assignment(models.Model):
    """A specific occurrence of a chore, given to a household member with a due date."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        DONE = "DONE", "Done"
        SKIPPED = "SKIPPED", "Skipped"

    chore = models.ForeignKey(
        Chore, on_delete=models.CASCADE, related_name="assignments"
    )
    assignee = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="assignments"
    )
    due_date = models.DateField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date", "id"]

    def __str__(self) -> str:
        return f"{self.chore.title} -> {self.assignee} ({self.get_status_display()})"

    def is_overdue(self, today: date | None = None) -> bool:
        today = today or timezone.localdate()
        return self.status == self.Status.PENDING and self.due_date < today

    def complete(self, user, note: str = "") -> "CompletionEvent":
        """Mark this assignment done and record a completion event.

        Idempotent: calling it again on an already-completed assignment returns
        the existing event instead of creating a duplicate (and does not spawn
        another recurring occurrence).
        """
        existing = self.completion_events.first()
        if self.status == self.Status.DONE and existing is not None:
            return existing
        self.status = self.Status.DONE
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])
        event = CompletionEvent.objects.create(
            assignment=self,
            completed_by=user,
            points_awarded=self.chore.points,
            note=note,
        )
        self.spawn_next()
        return event

    def skip(self) -> None:
        if self.status == self.Status.SKIPPED:
            return
        self.status = self.Status.SKIPPED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])
        self.spawn_next()

    def spawn_next(self) -> "Assignment | None":
        """Create the next occurrence of a recurring chore, if one is due.

        Does nothing unless the chore repeats, is active, and has no other
        pending assignment — so completing twice, or completing then skipping,
        never stacks up duplicates.
        """
        chore = self.chore
        if not (chore.is_recurring and chore.is_active):
            return None
        if chore.assignments.filter(status=self.Status.PENDING).exists():
            return None
        due = max(chore.next_due(self.due_date), timezone.localdate())
        return Assignment.objects.create(
            chore=chore,
            assignee=chore.next_assignee(self.assignee),
            due_date=due,
        )


class CompletionEvent(models.Model):
    """An immutable record that a chore assignment was completed."""

    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="completion_events"
    )
    completed_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="completion_events"
    )
    completed_at = models.DateTimeField(auto_now_add=True)
    points_awarded = models.PositiveIntegerField(default=0)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-completed_at", "-id"]

    def __str__(self) -> str:
        return f"{self.assignment.chore.title} by {self.completed_by} (+{self.points_awarded})"
