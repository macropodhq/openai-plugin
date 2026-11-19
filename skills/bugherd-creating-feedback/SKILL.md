---
name: bugherd-creating-feedback
description: Create BugHerd tasks from reviews, audits, checklists or user requests, including feedback pinned to a page element with a screenshot. Use when the user asks to log, report, raise or capture feedback, bugs or issues in BugHerd.
---

# Creating feedback in BugHerd

## Before you start

1. Find the project and call `get_project_details` (see `bugherd-basics`). Note its websites, statuses and, if you'll tag tasks, call `list_project_tags`.
2. Check the page URL is on one of the project's websites.
3. Pin every task about something on the page, with a screenshot. If you can run code, you can do this, even with no browser installed yet. See [Pinned feedback](#pinned-feedback).

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
- `bulk_create_tasks` creates up to 40 tasks in one project in a single call, and people get one email listing their new tasks instead of one per task. Use it for audit and checklist runs. Each result has its own `index` and either `task` or `error`, so check every result and retry only the ones that failed.

Before a large batch, tell the user how many tasks you're about to create and in which project.

## Pinned feedback

Every task about something on a page gets a pin and a screenshot whenever you can run code. That is the result BugHerd users expect. Pick the first route that works, and don't skip one because a later route looks easier:

1. **You can run code** (a shell, Python, Node). Use the capture script. If no browser is installed, install one: `pip install playwright && python -m playwright install chromium`. Fetching the page with curl or a fetch tool is not a substitute.
2. **You already drive a browser** (a browser tool, CDP, or a window the user controls). Measure there with `BugHerdMeasure.measure` and upload the viewport yourself.
3. **You can measure but can't capture pixels.** Leave `screenshot` as `auto` on a public page, and BugHerd takes the screenshot.
4. **You cannot run code at all**, or a browser failed to install or launch after you tried. Only then, use `element_selector` with `no_browser_reason`. These tasks never get a screenshot.

### The capture script

Call `get_pin_script` once. Download its `capture_script_url` and run it with the page, the `measure_script_url`, the viewport and one `--target` selector per task:

```bash
curl -sSo bugherd_capture.py "<capture_script_url>"
python bugherd_capture.py capture --url "<page url>" --measure-script-url "<measure_script_url>" \
  --viewport 1440x900 --target "h1.hero" --target "footer a.contact"
```

It blocks the BugHerd sidebar, scrolls to each element, waits for animations, measures it, and screenshots the viewport. Then:

1. Read `bugherd-capture/captures.json`. Fix any failing selector and run the capture again, so that every target succeeds.
2. Call `bulk_create_tasks` with the tasks in the same order as the captures. Set each task's `capture` to `captures[i].capture`, unchanged, and set `screenshot` to `upload`.
3. Save the response as JSON, then run `python bugherd_capture.py upload --captures bugherd-capture/captures.json --response response.json`.

For a signed-in page, pass the cookies as a Playwright storage state with `--storage-state`. For a phone, use `--device "iPhone 15"` or `--viewport 390x844`.

### Viewport

If the user named a device or a size, use that CSS viewport, such as 430×932 for an iPhone 15 Plus in portrait. Otherwise don't wait for an answer. Use 1440×900, or 390×844 if they asked for mobile feedback, and tell them which size you used and the others they can pick: desktop or laptop (1920×1080, 1440×900, 1366×768, 2560×1440) or mobile (390×844, 412×915, 360×800). Do not resize between the measurement and the screenshot.

### Measuring in your own browser

Before the page loads, block `sidebarv2.js` and `embed.js`. Use a browser profile without the BugHerd extension. If the window is one the user already uses, tell them to disable that extension, or the BugHerd tab will be in the screenshots.

Measure with `BugHerdMeasure.measure` and pass the packet unchanged as `capture`, with `screenshot` set to `upload`. The `create_task` response then carries a `screenshot_upload` form; screenshot the visible viewport before scrolling and post that JPEG to it. Leave `screenshot` as `auto` only when you can measure but cannot capture pixels, and only when the page is public. Use `none` when neither of you can reach the page, such as behind a login. Measure one element at a time when each task needs its own screenshot.

Do not ask for a password in the chat.

- **Login form.** If you can open a Chrome window, ask once whether to continue. The user signs in there. Then prefer headless Chrome: copy the cookies, close the window, and finish the pins and screenshots in headless Chrome. If you cannot move the session into headless Chrome, finish in the sign-in window. If you cannot open a window, say you cannot reach the page, and do not create tasks on the login form unless they asked for feedback on that form.
- **HTTP basic auth.** A 401, or Chrome's own username dialog. If you can open a Chrome window, ask once. The user signs in with that dialog. Stay in that window for the pins and the screenshots. Those credentials do not transfer to headless Chrome. If you cannot open a window, say the page is behind basic auth and stop. Do not create tasks.

### Last resort: no way to run code

Only when you cannot run code at all, or a browser failed to install or launch after you tried, pass `element_selector` (a normal CSS selector for one element, such as `section.pricing button.pay`) with `url` and `no_browser_reason` (`no_code_execution`, `browser_install_failed` or `browser_launch_failed`). Without that reason the task is refused. BugHerd fetches a public page itself and pins the centre of the element; send `page_html`, the full unedited document, only for a page BugHerd can't reach, such as localhost. There is no screenshot. A selector that matches more than one element does not place the pin, so make it specific. Content that JavaScript adds is not in the fetched document. Don't write `css_selector_info` by hand.

Tell the user these tasks have no screenshots. If the user says a pin is on the wrong element, ask which element they mean, then call `update_task` with a more specific `element_selector`.

If `get_pin_script` is missing from your tool list, your client is holding a cached copy of an older tool list. Reconnect the BugHerd MCP server or start a new chat so it reloads. If it is still missing, create page feedback with `url` and tell the user the task could not be pinned; don't retry in a loop, and don't attach a file with `get_attachment_upload_url` instead of pinning.

**Tell the user once, at the start of the run**, which of these your setup supports. Keep it brief. Follow [references/pinned-feedback.md](references/pinned-feedback.md) for the steps.

## After creating

- Check `pin_quality` on each created task. `pinned_with_screenshot` is the full result. For anything else, tell the user, and follow the `warnings` to upgrade the task.
- To give an existing task a screenshot, or to move its pin, measure the element again and call `update_task` with `capture` and `screenshot: "upload"`. Post the viewport JPEG to the returned `screenshot_upload` form; it replaces any older screenshot. Don't create a duplicate task.
- Read the `warnings` on each created task. They explain anything that didn't go to plan, such as a pin that wasn't saved, and how to fix it.
- Share the `view_in_bugherd_url` of each created task, or a summary for a batch.

## Attachments

To attach a local file, such as a log:

1. Call `get_attachment_upload_url` to get a `put_url` and `public_url` for each file.
2. HTTP PUT the file bytes to `put_url`. Send only the headers in `headers`. Do not add `x-amz-acl`: it is already in the URL, and S3 rejects the upload if you send it again.
3. Call `update_task_attachments` with `action: "add"` and `attachments: [{ file_name, url: public_url }]`.

For a file that's already online, pass its HTTPS `url` directly in step 3. This adds a file to the task. It does not pin the task, and it does not become the screenshot in the sidebar. That screenshot comes from the `screenshot_upload` form on the `create_task` response, described in the reference.
