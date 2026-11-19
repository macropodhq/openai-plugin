# Pinned feedback

A pinned task is attached to one element on a page. BugHerd shows the pin on that element in the sidebar, and on the task's screenshot.

Use these steps whenever you can run code. A terminal or sandbox that can run Python or Node counts: install a headless browser (`pip install playwright && python -m playwright install chromium`) and use the capture script that `get_pin_script` links as `capture_script_url`. It does steps 2 to 8 below in one command. Fetching the page with curl is not a substitute.

## What to expect from each setup

| Your setup | Pin | Screenshot |
|---|---|---|
| You can run code: the capture script, or a browser you drive, uploading the viewport | Accurate | Your screenshot, exactly matching the pin. Set `screenshot` to `upload` |
| You can run JavaScript, but you can't upload images, and the page is public | Accurate | BugHerd takes one about 2 minutes later. Leave `screenshot` as `auto` |
| Login form, and you can open a Chrome window | After the user signs in. Prefer to copy the cookies into headless Chrome and finish there | Your screenshot of the signed-in page |
| HTTP basic auth, and you can open a Chrome window | In that same window, after the user uses Chrome's dialog | Your screenshot from that window. The sign-in does not transfer to headless Chrome |
| Login form or basic auth, and you cannot open a window | Stop. Do not create tasks, unless they asked for feedback on the login form | None |
| Several elements measured together with `measureAll` | Accurate, without scrolling | Only for elements already on screen, and only when you cannot upload your own |
| Last resort: you cannot run code at all, or a browser failed to install or launch | Pin at the centre of the element `element_selector` matches. Needs `no_browser_reason` | None. Tell the user |
| No page HTML and no browser session | No pin. Create page feedback with `url` | None. An attached file is not the pin screenshot |

BugHerd also can't take its own screenshot when the organisation has screenshots turned off, or when more than an hour has passed since the task was created.

## Steps

### 1. Start a capture session

Call `get_pin_script` with the `project_id` once per run, even for many pages. It returns:

- `snippet`: JavaScript that defines `window.BugHerdMeasure`.
- `snippet_version`: keep it. Pass it to later `get_pin_script` calls and the snippet is left out when it hasn't changed.
- `measure_script_url`: the same code as a script URL, if loading a script is easier than evaluating the snippet.
- `instructions`: the current measuring rules. Follow them if they differ from this guide.

### 2. Set the viewport size

The pin and the screenshot both use the viewport size you measure at, and so does BugHerd's own screenshot. Use the device's CSS viewport, not its physical pixel size.

- If the user names a device, screen size, or breakpoint, use that. An iPhone 15 Plus in portrait is 430×932. A common phone is 390×844.
- Otherwise don't wait for an answer. Use 1440×900, or 390×844 if they asked for mobile feedback, and tell them which size you used and the others they can pick:
  - Desktop or laptop: 1920×1080, 1440×900, 1366×768, or 2560×1440.
  - Mobile: 390×844, 412×915, or 360×800.
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

- `upload`: you are posting the viewport yourself. This is the choice whenever you can capture pixels. The response includes a `screenshot_upload` form.
- `auto`: you can measure but cannot capture pixels, and the page is public. BugHerd photographs the live page itself at the measured scroll position, about two minutes later.
- `none`: neither of you can see the page, such as a page behind a login BugHerd does not have.

### 8. Upload the screenshot

With `screenshot: "upload"`, the `create_task` response carries `screenshot_upload`, along with the `expected_width` and `expected_height` of the viewport in CSS pixels (a device-pixel multiple is fine). No extra call is needed to start the upload. Then:

1. POST the JPEG to `upload_url` as multipart form data, with these fields: `key` set to `object_key`, `AWSAccessKeyId` set to `access_key_id`, `acl`, `policy`, `signature`, `Content-Type` set to `content_type`, and the image bytes in the `file` field.
2. PUT `callback_url` with the JSON body `{ "key": "<object_key>" }`. This attaches the screenshot to the task.

To replace a task's screenshot, measure again and call `update_task` with `capture` and `screenshot: "upload"`. Its response carries a fresh `screenshot_upload` form, and the new image replaces the old one.

## Many elements on one page

When you can upload a screenshot, measure one element at a time with `measure`, create that task, and upload that viewport before moving to the next element.

`BugHerdMeasure.measureAll([...])` measures several targets without scrolling. Use it only when you cannot upload screenshots. It returns a packet or `{ error }` for each. Pass each packet as a task's `capture` in `bulk_create_tasks`, and handle the errors separately. BugHerd then photographs only the elements that were already on screen, and only on a public page.

## Moving a pin

Measure the element again and pass the packet as `capture` to `update_task`, with `screenshot: "upload"` so the screenshot matches the new pin. The page URL comes from the capture. Without `screenshot: "upload"` the task keeps its existing screenshot. This needs permission to manage the task.

The same call upgrades a task that was pinned from HTML, or created as page feedback: it gets a measured pin and a screenshot. Prefer that to creating a duplicate task.

A pin placed from HTML has no screenshot to compare. When the user says it is on the wrong element, ask where it should be, then call `update_task` with `element_selector` and `no_browser_reason`. The pin moves to the centre of the matched element. Several matches move nothing.

## The older capture route

The response also includes `script_url`, `capture_url` and `token` for `BugHerdCapture`. After injecting `script_url` and calling `BugHerdCapture.configure({ endpoint: capture_url, token })`, `captureElement` and `captureText` return a `capture_id`. Pass it to `create_task` as `capture_id` instead of `capture`. Each id works once. Prefer `BugHerdMeasure` unless your browser tool can't evaluate the snippet.

## When something goes wrong

- **A warning says the task was created without a pin:** the packet was rejected, usually because it changed. Measure again and move the pin with `update_task`.
- **"Capture has already been used":** each `capture_id` works once. Capture again.
- **`get_pin_script` is not in your tool list:** start a new chat so the tools reload. Don't use `get_attachment_upload_url` in its place.
- **The pin looks off on the screenshot:** the screenshot was probably full-page, or the page scrolled between measuring and capturing. Measure again and take a viewport-only screenshot.
