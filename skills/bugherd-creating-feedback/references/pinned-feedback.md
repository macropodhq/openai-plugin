# Pinned feedback

A pinned task is attached to one element on a page. BugHerd shows the pin on that element in the sidebar, and on the task's screenshot.

Use these steps whenever you can open the page and run JavaScript. A client that cannot, such as a terminal, creates page feedback with `url` instead.

## What to expect from each setup

| Your setup | Pin | Screenshot |
|---|---|---|
| You can run JavaScript and upload a viewport screenshot | Accurate | Your screenshot, exactly matching the pin. Set `screenshot` to `none` |
| You can run JavaScript, but you can't upload images, and the page is public | Accurate | BugHerd takes one about 2 minutes later. Leave `screenshot` as `auto` |
| Login form, and you can open a Chrome window | After the user signs in. Prefer to copy the cookies into headless Chrome and finish there | Your screenshot of the signed-in page |
| HTTP basic auth, and you can open a Chrome window | In that same window, after the user uses Chrome's dialog | Your screenshot from that window. The sign-in does not transfer to headless Chrome |
| Login form or basic auth, and you cannot open a window | Stop. Do not create tasks, unless they asked for feedback on the login form | None |
| Several elements measured together with `measureAll` | Accurate, without scrolling | Only for elements already on screen, and only when you cannot upload your own |
| Fetched page HTML, and the element is in that document | Pin at the centre of the element `element_selector` matches | None. Pass `page_html` with the selector |
| No page HTML and no browser session | No pin. Create page feedback with `url` | None. An attached file is not the pin screenshot |

BugHerd also can't take its own screenshot when the organisation has screenshots turned off, or when more than an hour has passed since the task was created.

## Steps

### 1. Start a capture session

Call `prepare_pin` with the `project_id` once per run, even for many pages. It returns:

- `snippet`: JavaScript that defines `window.BugHerdMeasure`.
- `snippet_version`: keep it. Pass it to later `prepare_pin` calls and the snippet is left out when it hasn't changed.
- `measure_script_url`: the same code as a script URL, if loading a script is easier than evaluating the snippet.
- `instructions`: the current measuring rules. Follow them if they differ from this guide.

### 2. Set the viewport size

The pin and the screenshot both use the viewport size you measure at, and so does BugHerd's own screenshot. Use the device's CSS viewport, not its physical pixel size.

- If the user names a device, screen size, or breakpoint, use that. An iPhone 15 Plus in portrait is 430×932. A common phone is 390×844.
- Otherwise ask once which size to use, and use 1280×800 when they have no preference.
- If your browser can't be resized, carry on and mention the size you measured at in the task.

Don't resize between measuring and taking the screenshot.

### 3. Keep the BugHerd sidebar out of the screenshot

Block requests for `sidebarv2.js` and `embed.js` before the page loads. That stops the in-page widget. Blocking those scripts does not turn off the BugHerd browser extension.

Use a browser profile that does not have the extension. If the window is one the user already uses, tell them to disable the extension before you continue, or the BugHerd tab will be in the screenshots.

### 4. Sign in, when the page requires it

Do not ask for a password in the chat.

- **Login form.** If you can open a Chrome window, ask once whether to continue. The user signs in there. Then prefer headless Chrome: copy the cookies, close the window, and finish in headless Chrome. If you cannot move the session into headless Chrome, finish in the sign-in window. If you cannot open a window, say you cannot reach the page, and do not create tasks on the login form unless they asked for feedback on that form.
- **HTTP basic auth.** A 401, or Chrome's own username dialog. If you can open a Chrome window, ask once. The user signs in with that dialog. Stay in that window to measure, screenshot, and upload. Those credentials are not cookies, so closing the window drops the sign-in. If you cannot open a window, say the page is behind basic auth and stop.

Confirm the address is the page they named before you measure.

### 5. Measure the element

On each page load, evaluate the `snippet` in the page. It's safe to run more than once. Then evaluate:

```js
BugHerdMeasure.measure('#checkout .pay-button')
```

- The target is any CSS selector or element. If nothing matches, it throws, so try a different selector.
- To pin somewhere other than the centre, pass offsets from 0 to 1 inside the element: `measure(target, { x: 0.1, y: 0.5 })`.
- For a text change, pass `{ text: true }` to include the element's selected text.
- `measure` scrolls the element into view and returns a **packet**.

**Pass the packet unchanged.** It carries a checksum, so editing, rounding or rebuilding it makes BugHerd reject it.

### 6. Take the screenshot

Straight after `measure`, before anything scrolls, take a screenshot of the **visible viewport only**. A full-page screenshot puts the pin in the wrong place. Do this whenever you can capture pixels.

### 7. Create the task

Call `create_task` with the usual fields and `capture` set to the packet. The page URL and browser details come from the packet, so you don't need to pass `url`.

Set `screenshot`:

- `none`: you are uploading the viewport yourself, or BugHerd cannot see the page. This is the choice when you can capture pixels.
- `auto`: you can measure but cannot capture pixels, and the page is public. If you don't upload within 2 minutes, BugHerd takes one from the live page at the measured scroll position.

### 8. Upload the screenshot

Call `prepare_screenshot_upload` with `project_id` and `task_id`, within an hour of creating the task. It returns an upload form and the `expected_width` and `expected_height` of the viewport in CSS pixels (a device-pixel multiple is fine). Then:

1. POST the JPEG to `upload_url` as multipart form data, with these fields: `key` set to `object_key`, `AWSAccessKeyId` set to `access_key_id`, `acl`, `policy`, `signature`, `Content-Type` set to `content_type`, and the image bytes in the `file` field.
2. PUT `callback_url` with the JSON body `{ "key": "<object_key>" }`. This attaches the screenshot to the task.

A task that already has a screenshot refuses another. If the task's `screenshot.status` is `pending`, one is on its way, so don't upload.

## Many elements on one page

When you can upload a screenshot, measure one element at a time with `measure`, create that task, and upload that viewport before moving to the next element.

`BugHerdMeasure.measureAll([...])` measures several targets without scrolling. Use it only when you cannot upload screenshots. It returns a packet or `{ error }` for each. Pass each packet as a task's `capture` in `create_tasks`, and handle the errors separately. BugHerd then photographs only the elements that were already on screen, and only on a public page.

## Moving a pin

Measure the element again and pass the packet as `capture` to `update_task`. The page URL comes from the capture. The task keeps its existing screenshot. This needs permission to manage the task.

A pin placed from fetched HTML has no screenshot to compare. When the user says it is on the wrong element, ask where it should be, then call `update_task` with `element_selector` for that element and the same `page_html`. The pin moves to the centre of the matched element. Several matches move nothing.

## The older capture route

The response also includes `script_url`, `capture_url` and `token` for `BugHerdCapture`. After injecting `script_url` and calling `BugHerdCapture.configure({ endpoint: capture_url, token })`, `captureElement` and `captureText` return a `capture_id`. Pass it to `create_task` as `capture_id` instead of `capture`. Each id works once. Prefer `BugHerdMeasure` unless your browser tool can't evaluate the snippet.

## When something goes wrong

- **A warning says the task was created without a pin:** the packet was rejected, usually because it changed. Measure again and move the pin with `update_task`.
- **"Capture has already been used":** each `capture_id` works once. Capture again.
- **`prepare_pin` is not in your tool list:** start a new chat so the tools reload. Don't use `prepare_attachment_upload` in its place.
- **The pin looks off on the screenshot:** the screenshot was probably full-page, or the page scrolled between measuring and capturing. Measure again and take a viewport-only screenshot.
