---
name: bugherd-creating-feedback
description: Create BugHerd tasks from reviews, audits, checklists or user requests, including feedback pinned to a page element with a screenshot. Use when the user asks to log, report, raise or capture feedback, bugs or issues in BugHerd.
---

# Creating feedback in BugHerd

## Before you start

1. Find the project and call `get_project_details` (see `bugherd-basics`). Note its websites, statuses and, if you'll tag tasks, call `list_project_tags`.
2. Check the page URL is on one of the project's websites.
3. Pin the task when you can open the page and run JavaScript. Otherwise create page feedback. See [Pinned feedback](#pinned-feedback).

## Write good tasks

- **One issue per task.** Split a review into separate tasks so each can be assigned and closed on its own.
- **Description** (required, up to 2000 characters): what's wrong, what was expected, and how to see it. Include the checklist item or review rule it came from.
- **Title** (optional, up to 200 characters): short and specific, such as "Checkout button unreadable on mobile".
- **url**: the page the issue is on. For pinned tasks the page comes from the capture instead.
- **severity**: `critical`, `important`, `normal` or `minor`. Leave it out if you're unsure.
- **status**: leave it out to use the project's first column. Pass `"feedback"` to send it to the Feedback inbox for someone to triage, or a column name from the project's `statuses`. An unknown name is refused with the closest match.
- **tags** and **assignees**: use existing tags and project users. Assignees take `{ id }` or `{ email }`.
- **metadata**: key-value details such as the audit tool, rule id or console errors.

When the signed-in user is a client, BugHerd ignores title, severity, status, tags and assignees.

## One task or many

- `create_task` creates one task.
- `create_tasks` creates up to 40 tasks in one project in a single call, and people get one email listing their new tasks instead of one per task. Use it for audit and checklist runs. Each result has its own `index` and either `task` or `error`, so check every result and retry only the ones that failed.

Before a large batch, tell the user how many tasks you're about to create and in which project.

## Pinned feedback

When you can open the page and run JavaScript, pin every task. Call `begin_feedback_capture`, measure the element, and pass the packet as `capture`. Then upload the viewport with `prepare_feedback_screenshot`, or leave `screenshot` as `auto` and BugHerd takes one of a public page.

When you cannot run JavaScript, fetch the page HTML if the element is already in that document. Pass `element_selector` (a normal CSS selector for one element, such as `section.pricing button.pay`) and `page_html` (the full document), plus `url`. BugHerd builds the sidebar path and places the pin at the centre of the element. There is no screenshot. A selector that matches more than one element does not place the pin, so make it specific. Content that JavaScript adds is not in the fetched document; measure in a browser for those pages. Don't write `css_selector_info` by hand.

If the user looks at the page and says the pin is on the wrong element, call `update_task` with a more specific `element_selector` and the same `page_html`. Ask which element they mean before guessing between similar ones.

If `begin_feedback_capture` is missing from your tool list, start a new chat so the tools reload. Don't attach a file with `prepare_attachment_upload` instead of pinning.

A pin and a screenshot are most accurate when you can:

1. **Open the page in a browser session** and **run JavaScript in it**, to measure the element.
2. **Take a screenshot of the visible viewport and upload it** over HTTP.
3. **Reach the page the way its visitors do.** If the site needs a login, your browser session must be signed in.

When you can't upload a screenshot, BugHerd takes one itself for public pages that were measured in a browser. A pin from fetched HTML has no screenshot. When you have neither a browser nor page HTML, create page feedback.

**Tell the user once, at the start of the run**, which of these your setup supports and what that means for the pins and screenshots they'll get. Keep it brief and practical, for example:

> I can measure elements in your browser, but I can't upload screenshots, so BugHerd will take them for public pages. Your staging site needs a login, so tasks there will have accurate pins but no screenshot.

Follow [references/pinned-feedback.md](references/pinned-feedback.md) for the steps and how each setup behaves.

## After creating

- Read the `warnings` on each created task. They explain anything that didn't go to plan, such as a pin that wasn't saved, and how to fix it.
- Share the `view_in_bugherd_url` of each created task, or a summary for a batch.

## Attachments

To attach a local file, such as a log:

1. Call `prepare_attachment_upload` to get a `put_url` and `public_url` for each file.
2. HTTP PUT the file bytes to `put_url`. Send only the headers in `headers`. Do not add `x-amz-acl`: it is already in the URL, and S3 rejects the upload if you send it again.
3. Call `update_task_attachments` with `action: "add"` and `attachments: [{ file_name, url: public_url }]`.

For a file that's already online, pass its HTTPS `url` directly in step 3. This adds a file to the task. It does not pin the task, and it does not become the screenshot in the sidebar. That screenshot uses `prepare_feedback_screenshot`, described in the reference.
