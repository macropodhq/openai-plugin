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

When you can open the page and run JavaScript, pin every task and upload the viewport screenshot yourself.

Call `prepare_pin` once. Before the page loads, block `sidebarv2.js` and `embed.js`. Use a browser profile without the BugHerd extension. If the window is one the user already uses, tell them to disable that extension, or the BugHerd tab will be in the screenshots.

If the user named a device or a size, use that CSS viewport, such as 430×932 for an iPhone 15 Plus in portrait. Otherwise ask once which size to use, and use 1280×800 when they have no preference. Do not resize between the measurement and the screenshot.

Measure with `BugHerdMeasure.measure`, pass the packet unchanged as `capture`, screenshot the visible viewport before scrolling, and post that JPEG with `prepare_screenshot_upload`. Set `screenshot` to `none` so BugHerd does not take a second one. Leave `screenshot` as `auto` only when you can measure but cannot capture pixels, and only when the page is public. Measure one element at a time when each task needs its own screenshot.

Do not ask for a password in the chat.

- **Login form.** If you can open a Chrome window, ask once whether to continue. The user signs in there. Then prefer headless Chrome: copy the cookies, close the window, and finish the pins and screenshots in headless Chrome. If you cannot move the session into headless Chrome, finish in the sign-in window. If you cannot open a window, say you cannot reach the page, and do not create tasks on the login form unless they asked for feedback on that form.
- **HTTP basic auth.** A 401, or Chrome's own username dialog. If you can open a Chrome window, ask once. The user signs in with that dialog. Stay in that window for the pins and the screenshots. Those credentials do not transfer to headless Chrome. If you cannot open a window, say the page is behind basic auth and stop. Do not create tasks.

When you cannot run JavaScript, fetch the page HTML if the element is already in that document. Pass `element_selector` (a normal CSS selector for one element, such as `section.pricing button.pay`) and `page_html` (the full document), plus `url`. BugHerd builds the sidebar path and places the pin at the centre of the element. There is no screenshot. A selector that matches more than one element does not place the pin, so make it specific. Content that JavaScript adds is not in the fetched document; measure in a browser for those pages. Don't write `css_selector_info` by hand.

If the user looks at the page and says the pin is on the wrong element, call `update_task` with a more specific `element_selector` and the same `page_html`. Ask which element they mean before guessing between similar ones.

If `prepare_pin` is missing from your tool list, start a new chat so the tools reload. Don't attach a file with `prepare_attachment_upload` instead of pinning.

**Tell the user once, at the start of the run**, which of these your setup supports. Keep it brief. Follow [references/pinned-feedback.md](references/pinned-feedback.md) for the steps.

## After creating

- Read the `warnings` on each created task. They explain anything that didn't go to plan, such as a pin that wasn't saved, and how to fix it.
- Share the `view_in_bugherd_url` of each created task, or a summary for a batch.

## Attachments

To attach a local file, such as a log:

1. Call `prepare_attachment_upload` to get a `put_url` and `public_url` for each file.
2. HTTP PUT the file bytes to `put_url`. Send only the headers in `headers`. Do not add `x-amz-acl`: it is already in the URL, and S3 rejects the upload if you send it again.
3. Call `update_task_attachments` with `action: "add"` and `attachments: [{ file_name, url: public_url }]`.

For a file that's already online, pass its HTTPS `url` directly in step 3. This adds a file to the task. It does not pin the task, and it does not become the screenshot in the sidebar. That screenshot uses `prepare_screenshot_upload`, described in the reference.
