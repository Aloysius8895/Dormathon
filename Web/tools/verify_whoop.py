"""Check the local WHOOP site on desktop and mobile without outside requests."""
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "verification" / "whoop"
OUT.mkdir(parents=True, exist_ok=True)
PORT = 18083
BASE = f"http://127.0.0.1:{PORT}"
server = subprocess.Popen([sys.executable, str(ROOT / "serve.py"), "--port", str(PORT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    time.sleep(1)
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--use-gl=angle", "--use-angle=swiftshader"])
        for name, width, height in (("desktop", 1440, 1000), ("mobile", 390, 844)):
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            errors, failed, external = [], [], []
            def route_request(route):
                url = route.request.url
                if url.startswith(BASE) or url.startswith(("blob:", "data:")):
                    route.continue_()
                else:
                    external.append(url)
                    route.abort()
            page.route("**/*", route_request)
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("response", lambda response: failed.append(f"{response.status}: {response.url}") if response.status >= 400 else None)
            page.goto(BASE, wait_until="domcontentloaded", timeout=60000)
            page.locator(".loader.is-done").wait_for(timeout=90000)
            page.wait_for_timeout(1200)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(200)
            geometry = page.evaluate("""() => ({height: innerHeight, scrollY, hero: document.querySelector('.hero').getBoundingClientRect().height, variantTop: document.querySelector('.variant-panel').getBoundingClientRect().top})""")
            page.screenshot(path=str(OUT / f"{name}-hero.png"))
            page.get_by_role("button", name="Show Cobalt concept color").click()
            color = page.get_by_role("button", name="Show Cobalt concept color").get_attribute("aria-pressed")
            page.evaluate("window.scrollTo({top: document.querySelector('#assembly').offsetTop + (innerWidth <= 900 ? 750 : 300), behavior: 'instant'})")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT / f"{name}-assembly.png"))
            results.append({
                "viewport": name, "title": page.title(), "model_loaded": page.locator("#model-canvas").is_visible(),
                "selected_cobalt": color, "assembly_progress": page.locator("#explode-value").inner_text(),
                "parts": page.locator(".part-card").count(), "old_watch_text": "FS 60P" in page.locator("body").inner_text(), "geometry": geometry,
                "errors": errors, "http_errors": failed, "external_requests": external,
            })
            page.close()
        browser.close()
    (OUT / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
finally:
    server.terminate()
    server.wait(timeout=10)
