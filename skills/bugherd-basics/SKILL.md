---
name: bugherd-basics
description: Core BugHerd concepts for agents using the BugHerd MCP. Use before any BugHerd work to find the right project, and when the user asks about projects, websites, design assets, team members versus clients, or share links.
---

# BugHerd basics

BugHerd is a visual feedback tool. People leave feedback on a live website or a design file, and each piece of feedback becomes a **task** on a project's task board.

## Projects

A project is one piece of client or internal work. It holds:

- **Websites** (`sites`): the URLs where feedback can be left. Each has an `id`, `url`, `labels` and a `share_url`.
- **Design assets** (`assets`): images and PDFs that people can leave feedback on.
- **Statuses** (`statuses`): the columns on the task board, in order, such as Backlog, To Do, Doing, Done. Every project can name these differently.
- **People**: the users added to the project.

### Find the right project

1. If the user named a project or website, call `list_projects` with `name` or `site_url` to narrow it down.
2. Otherwise call `list_projects` with no filters and ask the user which one, unless only one fits.
3. Call `get_project_details` with the chosen `project_id` to get its websites, assets and statuses.

Pass `project_id` as a string, such as `"12345"`. When a page URL is involved, match it against the project's `sites` before creating or updating tasks there.

## Tasks

- `task_id` is the task's number within its project, the number people see in BugHerd. Update tools also accept the global task `id`.
- `status.name` is the board column the task is in. A task with no column is in **Feedback**, the inbox of new, untriaged feedback. Archived and closed tasks are off the board.
- `priority` is one of `not set`, `critical`, `important`, `normal`, `minor`. Tools that set it call it `severity`.
- `type` tells you how the task is anchored: `pinned comment` (pinned to an element), `text change`, `page feedback` (a page but no element), `screen recording` or `general`.

## People and access

People on a project are either **members** or **clients**:

- **Members** are the team doing the work, such as an agency's developers, designers and project managers. They see the full task board for their projects, and work on and manage tasks. Members with admin rights see every project in the organisation.
- **Clients** are the people the work is for. They leave feedback and see a reduced view of their projects.

Always say "members" and "clients" when talking to the user. Older parts of the API still say `guest` for clients, in field names such as `assign_guests`, `allow_guests_change_task_status`, `guest_visible` and `guests_see_all`, and in the `guest` role. Treat `guest` as "client" and translate it when you report back.

What clients see depends on project settings:

- `permission` controls whose feedback a client sees: `guests_see_self`, `guests_see_guests` or `guests_see_all`.
- `assign_guests` and `allow_guests_change_task_status` control whether clients can be assigned or change status.
- A task's `guest_visible` flag controls whether clients can see that task.

When the signed-in user is a client, tools return less. `get_project_details` leaves out websites, assets and statuses, `tag_names` is null on tasks, and `list_project_users` is refused. A permission error usually means the user's role doesn't allow the action, so tell the user rather than retrying.

Use `list_project_users` to find who is on a project. To add someone, call `update_project_users` with `action: "add"`, their `email` and a `role`: `member` for the team, or `guest` for a client. The role defaults to `guest`, so set it deliberately and confirm with the user which one they mean.

## Share links

- **Website**: each entry in `get_project_details` `sites` has a `share_url`. Anyone with the link can leave feedback on that site.
- **Task**: `share_url` on a task is a public link to that task. `view_in_bugherd_url` opens it in BugHerd for people with access, and `view_task_url` opens it on the original page.
- **Project**: `project_url` opens the task board for people with access.
- **Design asset**: each entry in `get_project_details` `assets` has a `share_url`. Anyone with the link can view the design and leave feedback on it.

Share links let people without accounts in, so only send them to people the user means to share with.

## Working well with BugHerd

- Read before you write: check the project's statuses, tags and people before setting them.
- Use exact status and tag names from the project. Ask if you're not sure which one the user means.
- Confirm with the user before changing many tasks at once, removing people or changing project settings.
- Comments can be visible to clients. See `bugherd-triage` before writing one.
