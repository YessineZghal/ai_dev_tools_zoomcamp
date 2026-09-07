# Choreo v2 — Review Fixes + Feature Additions (`task-v2.md`)

> **Status: ✅ complete.** Tasks A–E done. `uv run python manage.py test` →
> **92 passing** (was 60). All changes left uncommitted in the working tree.

Follow-up to [`task.md`](./task.md). Same rules: TDD, one behaviour per test,
`uv run python manage.py test` green after every task. **No git commits** —
changes stay in the working tree.

**Spec delta:** [`_docs/spec.md`](./_docs/spec.md) §9 non-goals are partially
lifted — recurring chores are now in scope.

---

## Task A: Review fixes

**A1 — Completion notes reachable from the UI** (review finding #1)

- `chores/views.py::assignment_complete`: drop `@require_POST`. On `GET`, render
  a small form (`chores/assignment_complete.html`) with an optional `note`
  textarea. On `POST`, call `assignment.complete(request.user, note=...)` and
  redirect to `_safe_next`. Quick one-click Complete buttons keep POSTing
  straight to this URL (no note) and still work.
- Add a "＋ note" link next to each quick Complete button
  (dashboard + chore list) pointing to the same URL via `GET`.
- Tests (`test_assignments.py`): `GET` renders the form (200, contains a
  `name="note"` field); `POST` with a note stores it on the `CompletionEvent`;
  the note shows on the History page.

**A2 — `chore_list` prefetch** (review finding #2)

- `chore_list`: replace `.prefetch_related("assignments__assignee")` with
  `Prefetch("assignments", queryset=Assignment.objects.filter(
  status=Assignment.Status.PENDING).select_related("assignee")
  .order_by("due_date"), to_attr="pending_assignments")`.
- `chore_list.html`: iterate `chore.pending_assignments`; `{% empty %}` now
  correctly shows "none".
- Test: a chore whose only assignments are DONE/SKIPPED renders "none" and does
  not list them.

---

## Task B: Recurring chores

**Model** (`chores/models.py`)

- `Chore.Recurrence` = `TextChoices`: `NONE`, `DAILY`, `WEEKLY`, `BIWEEKLY`,
  `MONTHLY`.
- `Chore.recurrence` = `CharField(choices, default=NONE)`.
- `Chore.rotate_assignee` = `BooleanField(default=False)` — on each new
  occurrence, hand the chore to the next household member (by username order,
  cyclic) instead of the same person.
- `Chore.is_recurring` property → `recurrence != NONE`.
- `Chore.next_due(after: date) -> date`: `DAILY` +1d, `WEEKLY` +7d,
  `BIWEEKLY` +14d, `MONTHLY` = `_add_one_month(after)` (clamp day to the last
  day of the target month). Module helper `_add_one_month(d)`.
- `Chore.next_assignee(current: User) -> User`: if `rotate_assignee`, the member
  after `current` in `household.members` (cyclic); else `current`. If `current`
  isn't a member, return the first member.

**Spawn logic**

- New method `Assignment.spawn_next() -> Assignment | None`: if
  `chore.is_recurring` and `chore.is_active` and the chore has **no** other
  `PENDING` assignment, create the next one:
  `due_date = max(chore.next_due(self.due_date), today)`,
  `assignee = chore.next_assignee(self.assignee)`. Return it (or `None`).
- Call `self.spawn_next()` at the end of both `Assignment.complete()` (after the
  idempotency guard, so completing twice spawns once) and `Assignment.skip()`.

**Management command** (`chores/management/commands/generate_recurring.py`)

- For every active recurring `Chore` with no `PENDING` assignment: create one,
  due `chore.next_due(last_assignment.due_date or today)`, assignee =
  `next_assignee` of the last assignment's assignee (or first member).
- Prints a one-line summary. Idempotent (running twice is a no-op).

**Form / templates**

- `ChoreForm`: add `recurrence`, `rotate_assignee` to `fields`.
- `chore_list.html`: show a recurrence badge (e.g. "weekly ⟳", "+ rotates").

**Tests** (`chores/tests/test_recurring.py`)

- `next_due` for each interval; `_add_one_month` clamps Jan 31 → Feb 28/29.
- Completing a `WEEKLY` assignment creates exactly one new `PENDING` assignment
  due +7 days, same assignee.
- `rotate_assignee=True` hands the next occurrence to the next member.
- Completing twice (idempotent complete) spawns only one.
- Skipping a recurring assignment also spawns the next.
- `recurrence=NONE` spawns nothing.
- Inactive recurring chore spawns nothing.
- `generate_recurring` command creates the missing occurrence and is a no-op on
  a second run.

---

## Task C: Household / members page

**View** `household_detail` at `/household/` (name `household_detail`)

- `@login_required`, household-scoped.
- Context: `household`, `memberships` — each annotated with
  `points_30d` (sum of `points_awarded` in the last 30 days) and
  `pending_count` (their `PENDING` assignments in this household),
  `my_membership`, and a bound `MembershipForm` for the current user.
- `POST` updates only `request.user`'s own `Membership.display_name`.

**Form** `MembershipForm(ModelForm)` — `fields = ["display_name"]`.

**Display name goes live** — use `membership.display_name` on:
- the members page,
- the dashboard leaderboard (`select_related("membership")` on
  `household.members`),
- keep username elsewhere (bounded change; note it in the README).

**Template** `chores/household_detail.html` — invite code, a members table
(name, points (30d), pending, joined), and the "your display name" form.
Link "Household" in the nav.

**Tests** (`chores/tests/test_household.py`)

- Members page lists all household members with correct points/pending counts,
  scoped to the household.
- `POST` changes the current user's `display_name`; cannot change another
  member's (form only ever binds `request.user`'s membership).
- Leaderboard shows `display_name` after it's changed.

---

## Task D: My Chores page + nav overdue badge

**View** `my_chores` at `/mine/` (name `my_chores`)

- `@login_required`, household-scoped to `request.user`.
- `?status=` filter: `pending` (default), `done`, `skipped`, `all`.
- Context: `assignments` (ordered by `due_date`), `status`, the choice list.

**Nav badge** — context processor `chores.context_processors.overdue_badge`:
for an authenticated user with a household, returns
`{"nav_overdue_count": <count of my PENDING assignments past due>}`; otherwise
`{}`. Register in `TEMPLATES["OPTIONS"]["context_processors"]`.

- `base.html`: add a "My chores" nav link with
  `{% if nav_overdue_count %}<span class="nav-badge">{{ nav_overdue_count }}</span>{% endif %}`.
- `style.css`: `.nav-badge` (small red pill).

**Templates** `chores/my_chores.html` — status filter (GET form) + a table
(chore, due, status, overdue flag, quick Complete for pending rows).

**Tests** (`chores/tests/test_my_chores.py`)

- Default view shows only my PENDING assignments; `?status=all` shows all mine;
  never shows other members' assignments.
- `?status=done` filters correctly.
- Context processor: `nav_overdue_count` equals my overdue count; absent for
  anonymous users and users without a household.

---

## Task E: Docs

- Update `README.md`: new "v2 additions" section, refresh the feature list,
  the test count, and the screens; note the partial display-name rollout and
  the `_docs/spec.md` non-goal change.
- Update `_docs/spec.md` §9 (recurring chores moved out of non-goals) and add
  the new models/fields to §6.
- New migration(s) for `Chore.recurrence` / `Chore.rotate_assignee`.
- Final: `uv run python manage.py check`,
  `makemigrations --check --dry-run`, `test`.
