from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch, Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    AssignmentForm,
    ChoreForm,
    HouseholdChoiceForm,
    MembershipForm,
    RegisterForm,
)
from .models import Assignment, Chore, CompletionEvent, household_of

LEADERBOARD_WINDOW_DAYS = 30
RECENT_ACTIVITY_LIMIT = 10


# --------------------------------------------------------------------------- #
# Auth & onboarding
# --------------------------------------------------------------------------- #
def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def household_setup(request):
    if household_of(request.user) is not None:
        return redirect("dashboard")
    if request.method == "POST":
        form = HouseholdChoiceForm(request.POST)
        if form.is_valid():
            form.attach_household(request.user)
            return redirect("dashboard")
    else:
        form = HouseholdChoiceForm()
    return render(request, "chores/household_setup.html", {"form": form})


@login_required
def household_detail(request):
    """The household roster: members with 30-day points and pending counts,
    the invite code, and a form for the current user to set their display name.
    """
    household, bounce = _household_or_setup(request)
    if bounce:
        return bounce

    my_membership = request.user.membership
    if request.method == "POST":
        form = MembershipForm(request.POST, instance=my_membership)
        if form.is_valid():
            form.save()
            return redirect("household_detail")
    else:
        form = MembershipForm(instance=my_membership)

    since = timezone.now() - timezone.timedelta(days=LEADERBOARD_WINDOW_DAYS)
    points = {
        row["completed_by"]: row["points"]
        for row in CompletionEvent.objects.filter(
            assignment__chore__household=household, completed_at__gte=since
        )
        .values("completed_by")
        .annotate(points=Sum("points_awarded"))
    }
    pending = {
        row["assignee"]: row["count"]
        for row in Assignment.objects.filter(
            chore__household=household, status=Assignment.Status.PENDING
        )
        .values("assignee")
        .annotate(count=Count("id"))
    }
    members = [
        {
            "membership": m,
            "points_30d": points.get(m.user_id, 0),
            "pending_count": pending.get(m.user_id, 0),
        }
        for m in household.memberships.select_related("user").order_by("display_name")
    ]
    return render(
        request,
        "chores/household_detail.html",
        {"household": household, "members": members, "form": form},
    )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _household_or_setup(request):
    """Return (household, None) or (None, redirect-to-setup)."""
    household = household_of(request.user)
    if household is None:
        return None, redirect("household_setup")
    return household, None


def _safe_next(request, fallback="dashboard"):
    """Return a local ``next`` path if one was supplied, else the fallback view name."""
    nxt = request.POST.get("next") or request.GET.get("next")
    if nxt and nxt.startswith("/") and not nxt.startswith("//"):
        return nxt
    return fallback


# --------------------------------------------------------------------------- #
# Dashboard (Feature 4)
# --------------------------------------------------------------------------- #
@login_required
def dashboard(request):
    household, bounce = _household_or_setup(request)
    if bounce:
        return bounce

    today = timezone.localdate()
    pending = Assignment.objects.filter(
        status=Assignment.Status.PENDING, chore__household=household
    ).select_related("chore", "assignee")

    my_pending = pending.filter(assignee=request.user).order_by("due_date")
    household_overdue = pending.filter(due_date__lt=today).order_by("due_date")

    recent_activity = (
        CompletionEvent.objects.filter(assignment__chore__household=household)
        .select_related("assignment__chore", "completed_by")
        .order_by("-completed_at", "-id")[:RECENT_ACTIVITY_LIMIT]
    )

    since = timezone.now() - timezone.timedelta(days=LEADERBOARD_WINDOW_DAYS)
    points_by_user = {
        row["completed_by"]: row["points"]
        for row in CompletionEvent.objects.filter(
            assignment__chore__household=household, completed_at__gte=since
        )
        .values("completed_by")
        .annotate(points=Sum("points_awarded"))
    }
    leaderboard = sorted(
        (
            {
                "member": m,
                "name": m.membership.display_name,
                "points": points_by_user.get(m.pk, 0),
            }
            for m in household.members
        ),
        key=lambda r: (-r["points"], r["name"].lower()),
    )

    return render(
        request,
        "chores/dashboard.html",
        {
            "household": household,
            "today": today,
            "my_pending": my_pending,
            "household_overdue": household_overdue,
            "recent_activity": recent_activity,
            "leaderboard": leaderboard,
        },
    )


MY_CHORES_FILTERS = [
    ("pending", "Pending"),
    ("done", "Done"),
    ("skipped", "Skipped"),
    ("all", "All"),
]


@login_required
def my_chores(request):
    """Every assignment for the current user, filterable by status."""
    household, bounce = _household_or_setup(request)
    if bounce:
        return bounce

    status = request.GET.get("status", "pending")
    if status not in dict(MY_CHORES_FILTERS):
        status = "pending"

    assignments = (
        Assignment.objects.filter(
            assignee=request.user, chore__household=household
        )
        .select_related("chore")
        .order_by("due_date", "id")
    )
    if status != "all":
        assignments = assignments.filter(status=status.upper())

    return render(
        request,
        "chores/my_chores.html",
        {
            "assignments": assignments,
            "status": status,
            "filters": MY_CHORES_FILTERS,
        },
    )


# --------------------------------------------------------------------------- #
# Chores CRUD (Feature 1)
# --------------------------------------------------------------------------- #
@login_required
def chore_list(request):
    household, bounce = _household_or_setup(request)
    if bounce:
        return bounce
    pending_qs = (
        Assignment.objects.filter(status=Assignment.Status.PENDING)
        .select_related("assignee")
        .order_by("due_date", "id")
    )
    chores = (
        Chore.objects.filter(household=household)
        .annotate(
            open_count=Count(
                "assignments",
                filter=Q(assignments__status=Assignment.Status.PENDING),
            )
        )
        .prefetch_related(
            Prefetch("assignments", queryset=pending_qs, to_attr="pending_assignments")
        )
        .order_by("title")
    )
    return render(request, "chores/chore_list.html", {"chores": chores})


@login_required
def chore_create(request):
    household, bounce = _household_or_setup(request)
    if bounce:
        return bounce
    if request.method == "POST":
        form = ChoreForm(request.POST)
        if form.is_valid():
            chore = form.save(commit=False)
            chore.household = household
            chore.save()
            return redirect("chore_list")
    else:
        form = ChoreForm()
    return render(
        request, "chores/chore_form.html", {"form": form, "verb": "New"}
    )


@login_required
def chore_update(request, pk):
    household, bounce = _household_or_setup(request)
    if bounce:
        return bounce
    chore = get_object_or_404(Chore, pk=pk, household=household)
    if request.method == "POST":
        form = ChoreForm(request.POST, instance=chore)
        if form.is_valid():
            form.save()
            return redirect("chore_list")
    else:
        form = ChoreForm(instance=chore)
    return render(
        request, "chores/chore_form.html", {"form": form, "verb": "Edit", "chore": chore}
    )


@login_required
def chore_delete(request, pk):
    household, bounce = _household_or_setup(request)
    if bounce:
        return bounce
    chore = get_object_or_404(Chore, pk=pk, household=household)
    if request.method == "POST":
        chore.delete()
        return redirect("chore_list")
    return render(request, "chores/chore_confirm_delete.html", {"chore": chore})


# --------------------------------------------------------------------------- #
# Assignments (Feature 2)
# --------------------------------------------------------------------------- #
@login_required
def assignment_create(request, pk):
    household, bounce = _household_or_setup(request)
    if bounce:
        return bounce
    chore = get_object_or_404(Chore, pk=pk, household=household)
    if request.method == "POST":
        form = AssignmentForm(request.POST, household=household)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.chore = chore
            assignment.save()
            return redirect("chore_list")
    else:
        form = AssignmentForm(household=household)
    return render(
        request, "chores/assignment_form.html", {"form": form, "chore": chore}
    )


def _get_scoped_assignment(request, pk):
    household = household_of(request.user)
    if household is None:
        return None
    return Assignment.objects.filter(
        pk=pk, chore__household=household
    ).select_related("chore").first()


@login_required
def assignment_complete(request, pk):
    """POST completes the assignment (optionally with a ``note``).

    GET shows a small form with an optional note field — the quick one-click
    Complete buttons POST here directly and skip the form.
    """
    assignment = _get_scoped_assignment(request, pk)
    if assignment is None:
        raise Http404
    if request.method == "POST":
        assignment.complete(request.user, note=request.POST.get("note", ""))
        return redirect(_safe_next(request))
    return render(
        request,
        "chores/assignment_complete.html",
        {"assignment": assignment, "next": _safe_next(request)},
    )


@login_required
@require_POST
def assignment_skip(request, pk):
    assignment = _get_scoped_assignment(request, pk)
    if assignment is None:
        raise Http404
    assignment.skip()
    return redirect(_safe_next(request))


# --------------------------------------------------------------------------- #
# Completion log (Feature 3)
# --------------------------------------------------------------------------- #
@login_required
def history(request):
    household, bounce = _household_or_setup(request)
    if bounce:
        return bounce
    events = (
        CompletionEvent.objects.filter(assignment__chore__household=household)
        .select_related("assignment__chore", "completed_by")
        .order_by("-completed_at", "-id")
    )
    member_id = request.GET.get("member")
    selected_member = None
    if member_id:
        events = events.filter(completed_by_id=member_id)
        selected_member = member_id
    return render(
        request,
        "chores/history.html",
        {
            "events": events,
            "members": household.members,
            "selected_member": selected_member,
        },
    )
