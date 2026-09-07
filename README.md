# Shared Household Chores Tool

A lightweight, full-stack Django web application designed for roommates to assign, track, and complete household chores with deadlines.

---

## Features

- **Passwordless Profile Switcher:** Switch between roommate profiles via a session-backed header dropdown without passwords.
- **Interactive Chore Board:** Main dashboard with instant filter tabs:
  - **All:** View all household chores.
  - **Assigned to Me:** Focus on tasks assigned to the active roommate profile.
  - **Pending:** Incomplete chores requiring attention.
  - **Completed:** History of finished chores.
- **Overdue Task Badges:** Visual indicators highlighting incomplete chores past their due date.
- **Chore Creation & Assignment:** Intuitive form to create tasks with title, description, assignee selection, and HTML5 date picker. Creation is automatically attributed to the active session roommate.
- **One-Click Done / Undo Toggle:** Mark chores as complete or incomplete instantly, with automatic completion timestamp tracking (`completed_at`).
- **Chore Deletion:** Quick removal of chores with CSRF-protected POST requests.
- **Data Seeding Commands:** Custom Django management commands to seed default roommates and realistic chore datasets for development and testing.
- **Responsive Design:** Clean, accessible layout built with modern vanilla CSS that adapts seamlessly to desktop and mobile screens.

---

## Tech Stack

- **Backend:** Python 3.12+, Django 5.x
- **Database:** SQLite (default)
- **Dependency Management:** [uv](https://docs.astral.sh/uv/)
- **Testing:** pytest, pytest-django

---

## Getting Started

### 1. Prerequisites

Ensure you have [uv](https://docs.astral.sh/uv/) installed on your machine.

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/CarlosRea/chores-app.git
cd chores-app
uv sync
```

### 3. Database Setup & Migrations

Run database migrations to initialize the schema:

```bash
uv run python manage.py migrate
```

### 4. Seed Initial Data

Populate default roommates (Alice, Bob, Charlie) and sample chores:

```bash
# Seed default roommates
uv run python manage.py seed_roommates

# Seed sample chores across various due dates and completion states
uv run python manage.py seed_chores
```

Both commands are idempotent and can be safely executed multiple times.

### 5. Run Development Server

Start the Django local development server:

```bash
uv run python manage.py runserver 127.0.0.1:8000
```

Open your browser and navigate to `http://127.0.0.1:8000/`.

---

## Running Tests

Run the complete test suite:

```bash
uv run pytest
```

To run a specific test file:

```bash
uv run pytest tests/test_views.py
uv run pytest tests/test_models.py
uv run pytest tests/test_commands.py
uv run pytest tests/test_templates.py
uv run pytest tests/test_forms.py
uv run pytest tests/test_session_switcher.py
```

---

## Project Structure

```
chores-app/
├── _docs/                  # Project specifications, backlog, and team role docs
├── chores/                 # Main Django application
│   ├── management/
│   │   └── commands/       # Management commands (seed_roommates, seed_chores)
│   ├── migrations/         # Database migrations
│   ├── templates/chores/   # HTML templates (base.html, chore_list.html, chore_form.html)
│   ├── context_processors.py # Session active roommate context processor
│   ├── forms.py            # ChoreForm ModelForm
│   ├── models.py           # Roommate and Chore models
│   ├── urls.py             # Application URL routes
│   └── views.py            # Board, switcher, create, toggle, and delete views
├── chores_project/         # Django project configuration
│   ├── settings.py         # Settings and installed apps
│   └── urls.py             # Root URL routing
├── tests/                  # Automated pytest test suite
│   ├── test_commands.py
│   ├── test_forms.py
│   ├── test_home.py
│   ├── test_models.py
│   ├── test_session_switcher.py
│   ├── test_templates.py
│   └── test_views.py
├── manage.py               # Django CLI entrypoint
├── pyproject.toml          # Project configuration and dependencies
└── README.md
```

---

## License

This project is licensed under the MIT License.
