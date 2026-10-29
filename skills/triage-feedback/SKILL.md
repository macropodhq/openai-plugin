---
name: triage-feedback
description: Find, summarize, and prioritize website feedback in BugHerd projects using the connected BugHerd MCP server. Use when the user asks to triage BugHerd feedback or review their BugHerd tasks.
---

# Triage BugHerd feedback

Use the connected BugHerd MCP tools. If the connection is unavailable, direct the user to connect BugHerd through the plugin's sign-in flow.

Resolve the requested project with `list_projects` when its ID is unknown. Use `get_project_details` to understand its board columns before filtering by status: status names are specific to each project.

Use `list_project_tasks` for project feedback and `list_my_tasks` for tasks assigned to **or created by** the connected user. The latter does not mean every returned task is assigned to that user. Follow pagination when the user needs a complete list; otherwise state the scope of the summary.

Use `get_task_details` when descriptions or discussion are needed to assess an issue. Summarize the feedback, distinguish suggested priorities from the existing task state, and include task identifiers and links returned by the tools.

When the user requests changes, use the currently advertised tools and their input schemas. Task numbers are local to their project, so pair them with the correct project ID. `add_comment` creates a Members Only comment when the organization supports private comments and a public comment otherwise; follow its attribution instructions.
