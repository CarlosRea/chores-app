# Project Specification: Shared Household Chores Tool

## 1. Overview
A lightweight, full-stack Django web application for roommates to manually assign, track, and complete one-off household chores with deadlines.

---

## 2. Core Decisions & Scope

| Feature | Decision |
|---|---|
| **Target Audience** | Roommates sharing a flat/house |
| **Assignment Model** | Direct manual assignment (assigner selects assignee + deadline) |
| **Recurrence** | One-off chores only (no recurring engine) |
| **Completion Flow** | Honor system (assignee or any roommate marks chore done) |
| **Authentication** | Passwordless profile switcher stored in session |
| **Tech Stack** | Django, SQLite, Django standard templates & forms |

---

## 3. Data Models

### `Roommate`
- `id`: Auto-increment primary key
- `name`: CharField (max_length=50, unique=True)

### `Chore`
- `id`: Auto-increment primary key
- `title`: CharField (max_length=150)
- `description`: TextField (blank=True)
- `assigned_by`: ForeignKey -> `Roommate` (related_name="assigned_chores")
- `assigned_to`: ForeignKey -> `Roommate` (related_name="my_chores")
- `due_date`: DateField
- `is_completed`: BooleanField (default=False)
- `completed_at`: DateTimeField (null=True, blank=True)
- `created_at`: DateTimeField (auto_now_add=True)

---

## 4. Key Routes & Views

| URL Pattern | View | Purpose |
|---|---|---|
| `/` | `chore_list` | Main task board with status & assignee filters |
| `/switch-user/<int:user_id>/` | `switch_user` | Sets `active_roommate_id` in session and redirects |
| `/chores/new/` | `chore_create` | Form to create a new chore (assigner defaults to active user) |
| `/chores/<int:pk>/toggle/` | `chore_toggle` | Toggle completed/pending status |
| `/chores/<int:pk>/delete/` | `chore_delete` | Remove a chore |

---

## 5. UI Requirements

- **Navbar / Top Bar:**
  - Active profile badge with a dropdown to quickly switch active roommate.
  - "New Chore" button.
- **Filters & Status:**
  - Filter tabs: *All*, *Assigned to Me*, *Pending*, *Completed*.
  - Visual indicator for overdue tasks (`due_date < today` and not completed).
- **Chore Cards / Rows:**
  - Title, due date, assignee, assigner badge, one-click "Done / Undo" toggle button.

---

## 6. Implementation Steps

1. **Setup:** Initialize Django project (`chores_project`) and app (`chores`).
2. **Models & Migrations:** Implement `Roommate` and `Chore` models; apply migrations.
3. **Seed Data:** Add 3–4 default roommates (e.g., Alice, Bob, Charlie).
4. **Session Middleware / Helper:** Context processor or helper to expose `active_roommate` to all templates.
5. **Forms & Views:** Build `ChoreForm` and corresponding CRUD views.
6. **Templates:** Create `base.html`, `chore_list.html`, and `chore_form.html` with clean, simple styling.
