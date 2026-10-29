---
name: bugherd-triage
description: Review and organise BugHerd feedback by changing status, assigning people, tagging, commenting and flagging what needs a human. Use when the user asks to triage, sort, assign, tag, prioritise, close or follow up on BugHerd tasks, or to reply on a task.
---

# Triaging BugHerd feedback

The agent takes the first pass; people make the calls that matter. Suggest, then act once the user agrees, unless they've told you to go ahead.

## 1. Gather context

1. `get_project_details`: the project's `statuses` (board columns, in order).
2. `list_project_users`: who can be assigned. Clients can only be assigned when the project's `assign_guests` (clients) setting is on.
3. `list_project_tags`: the tags the team already uses.
4. `list_project_tasks` with `status: "Feedback"` for new feedback, or the columns the user cares about. Use `view: "compact"` with `fields: ["description", "tag_names"]` to scan quickly, and page with `offset`.

## 2. Assess each task

Read anything unclear in full (see `bugherd-reading-tasks`). For each task, work out:

- **What it is**: bug, content change, design change, question or duplicate.
- **How urgent**: map to severity `critical`, `important`, `normal` or `minor`.
- **Who should own it**: from the area of the site, past assignments in similar tasks, or the user's guidance.
- **Whether a human needs to look**: unclear requests, scope or budget questions, conflicting feedback, anything a client should be asked about, and anything you're unsure of.

Present a short plan before changing anything: a list or table of tasks with the proposed status, severity, assignee and tags, plus a separate list of tasks needing human attention and why.

## 3. Apply changes

| Change | Tool |
|---|---|
| Status, severity, title, description, due date, client visibility | `update_task` |
| Assignees | `update_task_assignees` with `action` `add`, `remove` or `set` |
| Tags | `update_task_tags` with `action` `add`, `remove` or `set`. `set` with `[]` clears all tags |
| The same change on up to 50 tasks | `update_tasks` (bulk) |
| A reply or note | `add_comment` |

**Status names must match a column.** Use a name from `statuses`, `"feedback"` for the Feedback inbox, or `"archived"` or `"closed"` to take the task off the board. Matching ignores case. An unrecognised name is refused with the closest match and the full list, for example `Unknown status "Doen". Did you mean "Done"?`. Check the suggestion is what the user meant before retrying with it.

In `update_tasks`, assignees **replace** each task's existing assignees, while tags are **added** to existing tags. To add one assignee without removing others, use `update_task_assignees` with `action: "add"` per task.

## Comments

- Comments are visible to members only when the organisation has private comments, and visible to clients otherwise. Write every comment as if the client might read it.
- End agent-written comments with "(via {agent name})", such as "(via Claude)", unless the user says otherwise.
- Use comments to ask the reporter a clarifying question, record a decision or link to a fix. Don't comment just to say you've triaged a task.

## Care points

- Confirm before closing or archiving tasks, changing many tasks at once, or reassigning work someone has already started.
- `guest_visible: false` hides a task from clients. Only change visibility when the user asks.
- Finish with a summary of what changed, linking tasks by `view_in_bugherd_url`, and the list of tasks that need a person.
