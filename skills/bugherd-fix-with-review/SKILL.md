---
name: bugherd-fix-with-review
description: Take BugHerd feedback through to a code fix with a human approving each step, from triage and a proposed fix to the code change, pull request and sign-off. Use when the user asks to fix, resolve or work through BugHerd tasks in a codebase.
---

# Fixing BugHerd feedback with human review

The flow is: new feedback, then the agent suggests a fix, then a human approves, then the code change and pull request, then human sign-off. **Stop at each approval point.** Don't skip ahead because a fix looks obvious.

## Before you start

Agree these with the user once, and reuse them for the session:

- Which project and which tasks: a status such as "To Do", tasks assigned to them, or specific task numbers.
- Which statuses mean "in progress", "ready for review" and "done" on this project. Read the names from `get_project_details` `statuses`; don't guess.
- Whether you should move tasks and comment as you go, or leave BugHerd alone until they've reviewed.

## 1. Understand the task

Call `get_task_details` and follow `bugherd-reading-tasks`. Find the element in the code from `css_selector_info.html` and the page `url`, and look at `screenshot.pinned_url` if you can view images.

If the request is unclear, contradictory or needs a decision from the client, don't guess. Suggest a clarifying comment for the user to approve, and move on to the next task.

## 2. Propose the fix (approval point)

For each task, tell the user:

- what the feedback asks for, in one sentence
- where the change goes (files and components)
- what you'd change, and anything it might affect elsewhere
- how confident you are, and anything you couldn't check

Wait for approval. If the user changes the approach, follow theirs.

## 3. Make the change

- Keep each change to the task it fixes. Mention the task in the branch name or commit message, such as `Fix checkout button contrast (BugHerd #142)`.
- Run the project's tests and linters.
- If the user agreed, move the task to their "in progress" status with `update_task`.

## 4. Open the pull request (approval point)

Show the user the change before opening a pull request, unless they've said to go ahead. In the pull request description, link the task with its `view_in_bugherd_url`.

Then, if the user agreed:

- `add_comment` on the task with a short, client-friendly note and the pull request link, ending "(via {agent name})". Comments may be visible to clients, so describe the fix rather than the implementation.
- Move the task to their "ready for review" status.

## 5. Sign-off

A human decides when the work is done. Only move a task to the done status, or close it, when the user tells you to, for example after the pull request is merged or the client has checked it.

## Working through several tasks

Group tasks that touch the same code into one proposal, but keep one task per logical change so each can be signed off separately. Give the user a running list: proposed, approved, in pull request, needing clarification.
