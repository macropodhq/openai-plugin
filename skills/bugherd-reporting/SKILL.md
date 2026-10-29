---
name: bugherd-reporting
description: Summarise BugHerd activity and workload for standups, client meetings and status reports, covering what got done, what's stuck and who's doing what. Use when the user asks for a summary, report, update, recap or overview of BugHerd projects or tasks.
---

# Reporting on BugHerd activity

Reports should help someone walk into a standup or client meeting prepared. Lead with what matters (what's done, what's stuck, what needs a decision) rather than raw counts.

## Pick the tools

| Question | Tool |
|---|---|
| What's on my plate? | `list_my_tasks`: tasks assigned to or created by the user, across projects |
| What's open across all projects? | `list_all_tasks`, filtered by `status`, `assignee_email` or `search` |
| What's the state of one project? | `get_project_details` for statuses, then `list_project_tasks` by status |
| What happened since last time? | `list_project_activity` with `since` |
| How much got resolved, week by week? | `get_project_activity_report` |
| What's gone quiet? | `list_project_tasks` with `updated_before` and `sort_by: "updated_at"` |

Use `view: "compact"` on `list_project_tasks` for large projects, and page with `limit` and `offset` until you've seen every task. `pagination.total` tells you how many there are.

## Activity

`list_project_activity` lists actions on tasks between `since` and `until`. Each has a `type` (`task_created`, `comment_added` or `task_updated`), an `actor`, a `summary`, and `status_change.to` when the task moved. Filter with `task_id` or `actor_email`. Keep calling with `before_id` set to `pagination.next_before_id` while `has_more` is true, or you'll miss activity.

Activity records actions, not time spent, so don't present it as effort or hours.

## Activity report

`get_project_activity_report` needs:

- `since` (up to 366 days back) and optionally `until`
- `resolved_statuses`: the statuses that count as resolved on this project, such as `["Done"]` or `["UAT", "Done"]`. Ask the user if the project's `statuses` don't make it obvious.
- optionally `reopen_transitions`: backward moves to count as reopened, such as `[{ "from": "UAT", "to": "Doing" }]`

It returns:

- `weekly_resolved`: tasks that moved into a resolved status, per UTC week.
- `weekly_unresolved`: tasks recorded in a resolved status whose previous status isn't known. Despite the name, it doesn't count open tasks. Mention these separately rather than adding them to the resolved total.
- `column_change` and `reopen_transitions`: counts of moves between statuses.
- `status_counts`: current task counts by status, measured at `as_of`, not at the end of the period.

## A useful shape

1. **Headline**: one or two sentences on overall progress.
2. **Done**: tasks resolved in the period, grouped by theme or person.
3. **In progress**: who's working on what.
4. **Stuck or at risk**: tasks with no update for a while, tasks moved back, overdue `due_at`, and unassigned critical or important tasks.
5. **Needs a decision or client input**: questions waiting on someone.
6. **New feedback**: count and themes of tasks still in Feedback.

Link tasks with `view_in_bugherd_url`. For a client-facing summary, leave out internal names and notes unless the user wants them, and remember clients may not see every task.

## Accuracy

- Say which projects, dates and statuses the report covers.
- If you stopped paging early or a tool returned an error, say what's missing.
- Use counts from the tools; don't estimate.
