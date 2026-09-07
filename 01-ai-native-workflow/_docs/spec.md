# Choreo — Product Spec

> Homework 1 of the AI Dev Tools Zoomcamp. Turns the vague idea
> *"a tool for managing shared household chores"* into a concrete spec.

## 1. Problem

People who share a home (family, roommates, partners) lose track of who is
responsible for which chores, whether they were done, and whether the load is
shared fairly. Verbal agreements and paper lists fall apart.

## 2. Goal

A small web app where the members of one household can define chores, assign
them to each other with due dates, mark them done, and see at a glance what is
pending, what is overdue, and who has been pulling their weight.

## 3. Users & roles

- **Household member** — a registered user who belongs to exactly one
  household. Every member has the same permissions: they can create chores,
  assign them to anyone in the household (including themselves), and complete or
  skip any assignment. This is a trust-based tool for people who live together,
  not an org with managers.
- **Anonymous visitor** — can only see the login and register pages.

## 4. Core features (the spec settles on these 4)

### F1 — Chores CRUD
Members manage a catalogue of chores for their household.
- Fields: `title` (required), `description` (optional), `points` (positive
  integer, default 1 — a rough effort weight), `is_active` (default true).
- List view shows every chore in the household with its point value and a
  count of open assignments.
- Create / edit / delete via forms. Deleting a chore also removes its
  assignments (cascade).
- A chore always belongs to the creator's household; members of other
  households can never see or edit it.

### F2 — Assignments
Members assign a chore to a household member with a due date.
- Fields: `chore` (FK), `assignee` (FK → User, must be in the same household),
  `due_date` (date, required), `status` (`PENDING` / `DONE` / `SKIPPED`,
  default `PENDING`), `completed_at` (set when status leaves `PENDING`).
- "My chores" section lists the current user's `PENDING` assignments ordered
  by due date.
- An assignment is **overdue** when `status == PENDING` and
  `due_date < today`.
- Actions: **Complete** (→ `DONE`, records a completion event) and
  **Skip** (→ `SKIPPED`, no points).

### F3 — Completion log
Every completion is recorded as an immutable event, giving the household a
history.
- Fields: `assignment` (FK), `completed_by` (FK → User), `completed_at`
  (timestamp), `points_awarded` (copied from the chore's `points` at
  completion time), `note` (optional free text).
- History page lists completion events for the household, newest first,
  filterable by member.

### F4 — Dashboard
The landing page after login. One screen, four panels:
1. **My pending chores** — the current user's open assignments, overdue ones
   flagged.
2. **Household overdue** — every overdue assignment across the household.
3. **Recent activity** — the last 10 completion events.
4. **Leaderboard** — total `points_awarded` per member over the last 30 days,
   ranked.
The dashboard also shows the household's **invite code**.

## 5. Auth flow

- **Register** — username + password (Django's `UserCreationForm`), plus a
  choice:
  - *Create a new household* → provide a household name; the user becomes its
    first member.
  - *Join an existing household* → provide the 6-character invite code.
  On success the user is logged in and redirected to the dashboard.
- **Login / logout** — Django's built-in auth views.
- A logged-in user with no membership is sent to a "create or join household"
  page (defensive; normal registration always creates one).

## 6. Data model

```
Household(name, invite_code[unique, auto], created_at)
Membership(user[OneToOne→User], household[FK], display_name, joined_at)
Chore(household[FK], title, description, points[+int, default 1],
      is_active[bool, default True], created_at,
      recurrence[NONE|DAILY|WEEKLY|BIWEEKLY|MONTHLY, default NONE],  # v2
      rotate_assignee[bool, default False])                          # v2
Assignment(chore[FK], assignee[FK→User], due_date[date],
           status[PENDING|DONE|SKIPPED], completed_at[nullable],
           created_at)
CompletionEvent(assignment[FK], completed_by[FK→User],
                completed_at[auto], points_awarded[+int], note[text])
```

Helper: `Household.members` = users linked through `Membership`.
`invite_code` is 6 uppercase letters/digits, generated on first save.

## 7. Screens / URLs

| URL name | Path | Purpose |
|---|---|---|
| `dashboard` | `/` | F4 dashboard (login required) |
| `register` | `/accounts/register/` | F5 registration |
| `login` | `/accounts/login/` | Django auth |
| `logout` | `/accounts/logout/` | Django auth |
| `household_setup` | `/household/setup/` | create/join when no membership |
| `chore_list` | `/chores/` | F1 list |
| `chore_create` | `/chores/new/` | F1 create |
| `chore_update` | `/chores/<pk>/edit/` | F1 edit |
| `chore_delete` | `/chores/<pk>/delete/` | F1 delete |
| `assignment_create` | `/chores/<pk>/assign/` | F2 assign a chore |
| `assignment_complete` | `/assignments/<pk>/complete/` | F2 → DONE (+ event) |
| `assignment_skip` | `/assignments/<pk>/skip/` | F2 → SKIPPED |
| `history` | `/history/` | F3 completion log (`?member=<id>` filter) |

All views except register/login require authentication and scope every query
to `request.user`'s household.

## 8. UI

Server-rendered Django templates. One `base.html` with a top nav (Dashboard,
Chores, History, logout, current user). Plain hand-written CSS in
`chores/static/chores/style.css` — no CSS framework, no JavaScript, works
offline.

## 9. Non-goals (YAGNI)

- No email or push notifications.
- No REST API.
- No multiple households per user.
- No roles/permissions beyond "member".
- No real-time updates.
- No deployment config (runs on the Django dev server).

> **v2 update:** recurring / auto-rotating chores were originally cut here.
> They are now **in scope** — see §12.

## 12. v2 additions

- **Recurring chores.** `Chore.recurrence` (`NONE` / `DAILY` / `WEEKLY` /
  `BIWEEKLY` / `MONTHLY`) and `Chore.rotate_assignee` (bool). Completing or
  skipping a recurring assignment auto-creates the next occurrence — due date
  advanced by the interval (monthly clamps to the month length), assignee kept
  or rotated to the next member. Guarded so there is never more than one open
  occurrence per chore. `manage.py generate_recurring` is a cron-friendly
  safety net.
- **Completion notes reachable.** `assignment_complete` on `GET` shows a small
  form with an optional note; the quick one-click Complete buttons still `POST`
  straight through.
- **Household page** (`household_detail`, `/household/`). Member roster with
  30-day points and pending counts, the invite code, and a form to set your own
  `Membership.display_name`. Display names now show on the roster and the
  dashboard leaderboard (usernames elsewhere).
- **My Chores page** (`my_chores`, `/mine/`) with a status filter, plus a nav
  badge (`chores.context_processors.overdue_badge`) showing your overdue count.

## 10. Tech stack

- Python 3.12, Django (latest 5.x), SQLite.
- `uv` for the virtual environment and dependency management.
- Django's test framework (`django.test.TestCase` + `Client`).

## 11. Success criteria

- `uv run python manage.py runserver` serves the app.
- A user can register, create a household, add a chore, assign it, complete
  it, and see the completion on the dashboard and in the history.
- A second user joins with the invite code and sees the same household data.
- `uv run python manage.py test` passes, covering: model behaviour
  (invite code, overdue logic, completion event creation), auth/registration,
  household data isolation, chore CRUD, assignment lifecycle, and dashboard
  aggregates.
