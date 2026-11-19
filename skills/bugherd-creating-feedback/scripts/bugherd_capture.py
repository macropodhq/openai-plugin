#!/usr/bin/env python3
"""Measure page elements for BugHerd pins and screenshot each one.

Setup, once:
    pip install playwright && python -m playwright install chromium

Measure and screenshot:
    python bugherd_capture.py capture --url https://example.com/ \
        --measure-script-url <measure_script_url from get_pin_script> \
        --viewport 1440x900 --target "h1.hero" --target "footer a.contact"

Writes <out>/captures.json and one JPEG per target. Pass captures[i].capture unchanged as the
capture of task i in bulk_create_tasks, in the same order, with screenshot set to upload.
Save the bulk_create_tasks (or create_task) response as JSON, then:
    python bugherd_capture.py upload --captures bugherd-capture/captures.json --response response.json
"""

import argparse
import json
import mimetypes
import sys
import urllib.request
import uuid
from pathlib import Path

BLOCKED_SCRIPTS = ("**/sidebarv2.js*", "**/embed.js*")
NO_SMOOTH_SCROLL = "html, body { scroll-behavior: auto !important; }"


def read_targets(args):
    targets = [{"selector": selector} for selector in args.target or []]
    if args.targets:
        targets += json.loads(Path(args.targets).read_text())
    if not targets:
        sys.exit("Pass at least one --target selector or a --targets JSON file.")
    return targets


def capture(args):
    from playwright.sync_api import sync_playwright

    snippet = urllib.request.urlopen(args.measure_script_url, timeout=20).read().decode("utf-8")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    targets = read_targets(args)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        if args.device:
            options = dict(playwright.devices[args.device])
        else:
            width, height = (int(part) for part in args.viewport.lower().split("x"))
            options = {"viewport": {"width": width, "height": height}, "device_scale_factor": 1}
        if args.storage_state:
            options["storage_state"] = args.storage_state
        context = browser.new_context(bypass_csp=True, **options)
        for pattern in BLOCKED_SCRIPTS:
            context.route(pattern, lambda route: route.abort())
        page = context.new_page()
        page.goto(args.url, wait_until="networkidle", timeout=60000)
        page.add_style_tag(content=NO_SMOOTH_SCROLL)
        page.evaluate("() => {" + snippet + "\n; return Boolean(window.BugHerdMeasure); }")

        results = []
        for index, target in enumerate(targets):
            selector = target["selector"]
            measure_options = {key: target[key] for key in ("x", "y", "text") if key in target}
            try:
                page.evaluate("([s, o]) => { BugHerdMeasure.measure(s, o); }", [selector, measure_options])
                page.wait_for_timeout(args.settle_ms)
                packet = page.evaluate(
                    "([s, o]) => BugHerdMeasure.measure(s, { ...o, scroll: false })",
                    [selector, measure_options],
                )
                shot = out / f"{index}.jpg"
                page.screenshot(path=str(shot), type="jpeg", quality=85, full_page=False)
                results.append({"index": index, "selector": selector, "capture": packet, "screenshot": str(shot)})
            except Exception as error:  # noqa: BLE001
                results.append({"index": index, "selector": selector, "error": str(error).splitlines()[0]})
        browser.close()

    manifest = out / "captures.json"
    manifest.write_text(json.dumps({"page_url": args.url, "captures": results}, indent=2))
    failed = [item for item in results if "error" in item]
    print(f"Measured {len(results) - len(failed)} of {len(results)} targets. Wrote {manifest}")
    for item in failed:
        print(f"  target {item['index']} ({item['selector']}): {item['error']}")


def multipart(fields, file_field, file_path):
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in fields:
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    content_type = mimetypes.guess_type(file_path)[0] or "image/jpeg"
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="screenshot.jpg"\r\n'
        f"Content-Type: {content_type}\r\n\r\n".encode()
    )
    parts.append(Path(file_path).read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def upload_one(form, screenshot):
    fields = [
        ("key", form["object_key"]),
        ("AWSAccessKeyId", form["access_key_id"]),
        ("acl", form["acl"]),
        ("policy", form["policy"]),
        ("signature", form["signature"]),
        ("Content-Type", form["content_type"]),
    ]
    body, content_type = multipart(fields, form.get("file_field", "file"), screenshot)
    post = urllib.request.Request(form["upload_url"], data=body, headers={"Content-Type": content_type})
    urllib.request.urlopen(post, timeout=60)
    callback = urllib.request.Request(
        form["callback_url"],
        data=json.dumps({"key": form["object_key"]}).encode(),
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    urllib.request.urlopen(callback, timeout=60)


def upload(args):
    captures = json.loads(Path(args.captures).read_text())["captures"]
    response = json.loads(Path(args.response).read_text())
    if "results" in response:
        forms = [(item["index"], item.get("task", {}).get("screenshot_upload")) for item in response["results"]]
    else:
        forms = [(args.index, response.get("screenshot_upload"))]

    for index, form in forms:
        shot = captures[index].get("screenshot") if index < len(captures) else None
        if not form or not shot:
            print(f"task {index}: skipped (no screenshot_upload form or no screenshot)")
            continue
        try:
            upload_one(form, shot)
            print(f"task {index}: screenshot attached")
        except Exception as error:  # noqa: BLE001
            print(f"task {index}: upload failed: {error}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    capture_parser = commands.add_parser("capture", help="Measure targets and screenshot each one.")
    capture_parser.add_argument("--url", required=True)
    capture_parser.add_argument("--measure-script-url", required=True)
    capture_parser.add_argument("--viewport", default="1440x900", help="CSS viewport, such as 1440x900 or 390x844.")
    capture_parser.add_argument("--device", help='Playwright device name instead of --viewport, such as "iPhone 15".')
    capture_parser.add_argument("--target", action="append", help="CSS selector for one element. Repeat per task.")
    capture_parser.add_argument("--targets", help='JSON list of {"selector", "x", "y", "text"} objects.')
    capture_parser.add_argument("--storage-state", help="Playwright storage state JSON with the signed-in cookies.")
    capture_parser.add_argument("--settle-ms", type=int, default=800, help="Wait after scrolling, for animations.")
    capture_parser.add_argument("--out", default="bugherd-capture")
    capture_parser.set_defaults(handler=capture)

    upload_parser = commands.add_parser("upload", help="Post each screenshot to its screenshot_upload form.")
    upload_parser.add_argument("--captures", required=True)
    upload_parser.add_argument("--response", required=True, help="Saved bulk_create_tasks or create_task response.")
    upload_parser.add_argument("--index", type=int, default=0, help="Capture index for a single create_task response.")
    upload_parser.set_defaults(handler=upload)

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
