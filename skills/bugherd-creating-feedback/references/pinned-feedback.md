# Pinned feedback

A pinned task is attached to one element on a page. BugHerd shows the pin on that element in the sidebar, and on the task's screenshot.

These steps need `begin_feedback_capture`, which only appears when pinned feedback is enabled for the user's organisation.

## What to expect from each setup

| Your setup | Pin | Screenshot |
|---|---|---|
| Browser session that can run JavaScript, plus you upload a viewport screenshot | Accurate | Your screenshot, exactly matching the pin |
| Browser session that can run JavaScript, but you can't upload images | Accurate | BugHerd takes one about 2 minutes later, if the page is public |
| Page needs a login, or is on localhost or a private network | Accurate, if your browser is signed in | Only if you upload one. BugHerd can't reach the page |
| Several elements measured together with `measureAll` | Accurate | BugHerd takes one only for elements that were on screen |
| No browser session | No pin. Create page feedback with `url` | None from BugHerd. Attach your own image if you have one |

BugHerd also can't take its own screenshot when the organisation has screenshots turned off, or when more than an hour has passed since the task was created.

## Steps

### 1. Start a capture session

Call `begin_feedback_capture` with the `project_id` once per run, even for many pages. It returns:

- `snippet`: JavaScript that defines `window.BugHerdMeasure`.
- `snippet_version`: keep it. Pass it to later `begin_feedback_capture` calls and the snippet is left out when it hasn't changed.
- `measure_script_url`: the same code as a script URL, if loading a script is easier than evaluating the snippet.
- `instructions`: the current measuring rules. Follow them if they differ from this guide.

### 2. Set the viewport size

The pin and the screenshot both use the viewport size you measure at, and so does BugHerd's own screenshot. Browser panels inside editors are often narrow, which makes many sites switch to their mobile layout.

- If the user asks for a particular device, screen size or breakpoint, use that, for example 390×844 for a phone.
- Otherwise, resize the viewport to a desktop size such as 1280×800 before loading the page.
- If your browser can't be resized, carry on and mention the size you measured at in the task.

Don't resize between measuring and taking the screenshot.

### 3. Measure the element

On each page load, evaluate the `snippet` in the page. It's safe to run more than once. Then evaluate:

```js
BugHerdMeasure.measure('#checkout .pay-button')
```

- The target is any CSS selector or element. If nothing matches, it throws, so try a different selector.
- To pin somewhere other than the centre, pass offsets from 0 to 1 inside the element: `measure(target, { x: 0.1, y: 0.5 })`.
- For a text change, pass `{ text: true }` to include the element's selected text.
- `measure` scrolls the element into view and returns a **packet**.

**Pass the packet unchanged.** It carries a checksum, so editing, rounding or rebuilding it makes BugHerd reject it.

### 4. Take the screenshot, if you can

Straight after `measure`, before anything scrolls, take a screenshot of the **visible viewport only**. A full-page screenshot puts the pin in the wrong place.

### 5. Create the task

Call `create_task` with the usual fields and `capture` set to the packet. The page URL and browser details come from the packet, so you don't need to pass `url`.

Set `screenshot`:

- `auto` (the default): if you don't upload a screenshot within 2 minutes, BugHerd takes one from the live page at the measured scroll position.
- `none`: BugHerd won't take one. Use it when BugHerd can't see what you see, such as a page behind a login or content that only appears after an interaction.

### 6. Upload the screenshot

Call `prepare_feedback_screenshot` with `project_id` and `task_id`, within an hour of creating the task. It returns an upload form and the `expected_width` and `expected_height` of the viewport in CSS pixels (a device-pixel multiple is fine). Then:

1. POST the JPEG to `upload_url` as multipart form data, with these fields: `key` set to `object_key`, `AWSAccessKeyId` set to `access_key_id`, `acl`, `policy`, `signature`, `Content-Type` set to `content_type`, and the image bytes in the `file` field.
2. PUT `callback_url` with the JSON body `{ "key": "<object_key>" }`. This attaches the screenshot to the task.

A task that already has a screenshot refuses another. If the task's `screenshot.status` is `pending`, one is on its way, so don't upload.

## Many elements on one page

`BugHerdMeasure.measureAll([...])` measures several targets without scrolling. It returns a packet or `{ error }` for each. Pass each packet as a task's `capture` in `create_tasks`, and handle the errors separately.

Because nothing scrolls, BugHerd only takes screenshots for elements that were on screen. For elements further down the page, use `measure` and `create_task` one at a time, so each one is scrolled into view and gets its own screenshot.

## Moving a pin

Measure the element again and pass the packet as `capture` to `update_task`. The page URL comes from the capture. The task keeps its existing screenshot. This needs permission to manage the task.

## The older capture route

The response also includes `script_url`, `capture_url` and `token` for `BugHerdCapture`. After injecting `script_url` and calling `BugHerdCapture.configure({ endpoint: capture_url, token })`, `captureElement` and `captureText` return a `capture_id`. Pass it to `create_task` as `capture_id` instead of `capture`. Each id works once. Prefer `BugHerdMeasure` unless your browser tool can't evaluate the snippet.

## When something goes wrong

- **A warning says the task was created without a pin:** the packet was rejected, usually because it changed. Measure again and move the pin with `update_task`.
- **"Capture has already been used":** each `capture_id` works once. Capture again.
- **"Pinned feedback capture is not enabled":** create page feedback with `url` instead.
- **The pin looks off on the screenshot:** the screenshot was probably full-page, or the page scrolled between measuring and capturing. Measure again and take a viewport-only screenshot.
