"""Domain models for Choreo — a shared household chores manager.

The object graph is:

    Household 1--* Membership *--1 User
    Household 1--* Chore 1--* Assignment *--1 User (assignee)
    Assignment 1--* CompletionEvent *--1 User (completed_by)
"""

import secrets
from datetime import date

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
        return User.objects.filter(membership__household=self).order_by("username")


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
    """A recurring task the household cares about (the catalogue entry)."""

    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name="chores"
    )
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    points = models.PositiveIntegerField(
        default=1, help_text="Rough effort weight, used for the leaderboard."
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


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
        the existing event instead of creating a duplicate.
        """
        existing = self.completion_events.first()
        if self.status == self.Status.DONE and existing is not None:
            return existing
        self.status = self.Status.DONE
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])
        return CompletionEvent.objects.create(
            assignment=self,
            completed_by=user,
            points_awarded=self.chore.points,
            note=note,
        )

    def skip(self) -> None:
        self.status = self.Status.SKIPPED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])


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
