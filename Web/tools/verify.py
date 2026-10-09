"""Render the local mirror and record loading and request health."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "verification"
OUT.mkdir(exist_ok=True)
server = subprocess.Popen([sys.executable, str(ROOT / "serve.py"), "--port", "18082"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    time.sleep(1)
    reports = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--use-gl=angle", "--use-angle=swiftshader"])
        for label, width, height in (("desktop", 1440, 1000), ("mobile", 390, 844)):
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            failed = []
            errors = []
            external = []
            def route_request(route):
                url = route.request.url
                if url.startswith(("http://127.0.0.1:18082/", "blob:", "data:")):
                    route.continue_()
                else:
                    external.append(url)
                    route.abort()
            page.route("**/*", route_request)
            page.on("requestfailed", lambda req: failed.append({"url": req.url, "reason": req.failure}))
            page.on("response", lambda response: errors.append({"url": response.url, "status": response.status}) if response.status >= 400 else None)
            page.goto("http://127.0.0.1:18082/", wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(15000)
            first = {"loader_visible": page.locator("#loader").is_visible(), "canvas": page.locator("canvas").count(), "title": page.title(), "body_text": page.locator("body").inner_text()[:600]}
            page.screenshot(path=str(OUT / f"{label}-initial.png"))
            for _ in range(8):
                page.mouse.wheel(0, height * 0.8)
                page.wait_for_timeout(600)
            page.screenshot(path=str(OUT / f"{label}-scrolled.png"))
            reports.append({"viewport": label, "initial": first, "request_failed": failed, "http_errors": errors, "external_requests": external, "final_scroll": page.evaluate("window.scrollY"), "page_height": page.evaluate("document.documentElement.scrollHeight")})
            page.close()
        browser.close()
    (OUT / "results.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(json.dumps(reports, indent=2))
finally:
    server.terminate()
    server.wait(timeout=10)
