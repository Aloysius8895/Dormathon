"""Check that the original page renders while WHOOP is the visible 3D model."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "verification" / "overlay"
OUT.mkdir(parents=True, exist_ok=True)
server = subprocess.Popen([sys.executable, str(ROOT / "serve.py"), "--port", "18084"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    time.sleep(1)
    reports = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--use-gl=angle", "--use-angle=swiftshader"])
        for label, width, height in (("desktop", 1440, 1000), ("mobile", 390, 844)):
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            errors = []
            failures = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("response", lambda response: failures.append({"url": response.url, "status": response.status}) if response.status >= 400 else None)
            page.goto("http://127.0.0.1:18084/", wait_until="domcontentloaded", timeout=90000)
            page.wait_for_selector("body.whoop-model-ready", timeout=90000)
            page.wait_for_timeout(5000)
            page.screenshot(path=str(OUT / f"{label}-hero.png"))
            initial = page.evaluate("""() => ({title: document.title, model: document.querySelector('.whoop-overlay-canvas')?.getAttribute('aria-label'), oldCanvasHidden: [...document.querySelectorAll('#canvas-wrapper canvas')].filter(c => !c.classList.contains('whoop-overlay-canvas')).every(c => getComputedStyle(c).visibility === 'hidden'), sectionCount: document.querySelectorAll('[data-section]').length, loaderVisible: !!document.querySelector('#loader') && getComputedStyle(document.querySelector('#loader')).opacity !== '0'})""")
            disassembly = page.locator('[data-webgl="Disassembly"]').first
            if label == 'desktop' and disassembly.count():
                page.evaluate('document.querySelector("[data-webgl=Disassembly]").scrollIntoView()')
                page.wait_for_timeout(1000)
                page.screenshot(path=str(OUT / f"{label}-disassembly.png"))
            reports.append({"viewport": label, "initial": initial, "variant": page.locator('.whoop-overlay-canvas').get_attribute('data-variant'), "errors": errors, "http_errors": failures, "final_scroll": page.evaluate('scrollY')})
            page.close()
        browser.close()
    (OUT / "results.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(json.dumps(reports, indent=2))
    for report in reports:
        assert report["initial"]["model"] == "WHOOP 3D model", report
        assert report["initial"]["oldCanvasHidden"], report
        assert report["initial"]["sectionCount"] == 14, report
        assert report["variant"] == "graphite", report
        assert not report["errors"], report
finally:
    server.terminate()
    server.wait(timeout=10)
