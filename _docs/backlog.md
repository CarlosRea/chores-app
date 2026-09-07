# Backlog: Shared Household Chores Tool

## 1. Project Initialization and Test Setup
Goal: Initialize an empty Django project configured with SQLite and verify it with a passing test.
Description: Set up a new Django project and an application named `chores` using SQLite as the default database. Configure settings with required apps and defaults. Add a simple automated test verifying that the test runner executes and passes.

## 2. Roommate and Chore Data Models
Goal: Define the database schema for roommates and chores with initial migrations.
Description: Create `Roommate` (with a unique name) and `Chore` (with title, description, assigned_by, assigned_to, due_date, is_completed, and timestamps) models in the `chores` app. Establish foreign key relationships linking chores to assigners and assignees. Generate and apply the database migrations.

## 3. Seed Initial Roommates Data
Goal: Provide a command to populate default roommate profiles for development and testing.
Description: Implement a custom Django management command that creates initial sample roommates (e.g., Alice, Bob, Charlie) if they do not already exist. Ensure the command is idempotent so running it multiple times will not create duplicates. Add automated tests to verify that the seed command populates the database correctly.

## 4. Active Roommate Session Switcher
Goal: Allow users to select an active roommate profile and persist it across requests without passwords.
Description: Implement an endpoint that saves an `active_roommate_id` into the Django session and redirects back to the referring page. Create a context processor that injects the active `Roommate` object into all template rendering contexts. Write automated tests to verify that switching profiles correctly updates session state and context availability.

## 5. Chore List View and Filter Tabs
Goal: Render a task board displaying chores with status and assignee filter options.
Description: Build a view and template that lists chores categorized into tabs such as All, Assigned to Me, Pending, and Completed. Include visual styling or badges for overdue chores where the due date is in the past and status is incomplete. Add unit tests to verify proper queryset filtering based on query parameters.

## 6. Chore Creation Form and View
Goal: Enable roommates to create and assign new chores with due dates.
Description: Implement a Django `ModelForm` for the `Chore` model capturing title, description, assignee, and due date. Create a view that processes form submissions, automatically setting `assigned_by` to the currently active roommate. Add unit tests covering form validation and successful chore creation.

## 7. Chore Toggle and Delete Actions
Goal: Enable roommates to toggle chore completion status and delete chores.
Description: Create view endpoints to toggle a chore's `is_completed` flag and record completion timestamps, as well as an endpoint to delete a chore. Restrict state-changing actions to POST requests with proper CSRF protection and redirect back to the chore list. Write unit tests to verify status toggling and chore deletion behavior.

## 8. Base Template and UI Styling
Goal: Create a clean, responsive layout featuring navigation, profile switcher, and flash messages.
Description: Build a shared `base.html` template using clean CSS or a lightweight framework to provide a consistent header, navigation bar, and message alerts. Integrate the roommate switcher dropdown into the header alongside a "New Chore" action button. Ensure all views extend this base layout and render cleanly across desktop and mobile screens.
