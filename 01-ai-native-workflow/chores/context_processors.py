"""Template context available on every page."""

from django.utils import timezone

from .models import Assignment, household_of


def overdue_badge(request):
    """Expose ``nav_overdue_count`` — the current user's overdue pending
    assignments — so the nav can show a badge. Empty for anonymous users or
    users without a household.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}
    household = household_of(user)
    if household is None:
        return {}
    count = Assignment.objects.filter(
        assignee=user,
        chore__household=household,
        status=Assignment.Status.PENDING,
        due_date__lt=timezone.localdate(),
    ).count()
    return {"nav_overdue_count": count}
