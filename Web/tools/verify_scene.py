"""Check that WHOOP sits inside the original WebGL scene and follows its animations."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "verification" / "scene"
OUT.mkdir(parents=True, exist_ok=True)
PORT = 18085
# Missing from the original mirror; unrelated to the WHOOP model.
KNOWN_MISSING = "/assets/the-watch/img/parts/"

# Keep a handle on the page module the router loaded.
EXPOSE = r"""async () => {
  const entry = performance.getEntriesByType('resource').find(e => /\/assets\/the-watch\.[^/]+\.js$/.test(e.name));
  window.__project = (await import(entry.name)).project;
}"""

PROBE = """() => {
  const project = window.__project;
  const scene = project.webgl.scene, watch = scene.watch;
  const anchor = watch.getObjectByName('WHOOP_Anchor');
  const pivots = Object.fromEntries((anchor?.children || []).map(p => [p.name, {z: +p.position.z.toFixed(4), ry: +p.rotation.y.toFixed(3), visible: p.visible}]));
  let visibleWatchMeshes = 0;
  watch.traverse(n => { if (n.isMesh && n.layers.test(project.webgl.camera.layers) && !anchor?.getObjectById(n.id) && n.material?.visible !== false && n !== scene.laserBeam) visibleWatchMeshes++; });
  const section = project.webgl.sectionsController.sections?.find(s => s.progressWebgl > 0 && s.progressWebgl < 1);
  return {
    anchored: !!anchor && anchor.parent === watch,
    watchRotation: [watch.rotation.x, watch.rotation.y, watch.rotation.z].map(v => +v.toFixed(3)),
    watchPosition: [watch.position.x, watch.position.y, watch.position.z].map(v => +v.toFixed(3)),
    visibleWatchMeshes,
    footerWhoops: scene.watchesGroup.watchesInsideGroup.children.filter(w => w.children[0].getObjectByName('WHOOP_Anchor')).length,
    section: section ? {name: section.name, progress: +section.progressWebgl.toFixed(3)} : null,
    pivots,
    variant: document.body.dataset.whoopVariant,
  };
}"""

DISASSEMBLY = "__project.webgl.sectionsController.sections.find(x => x.name === 'Disassembly')"
PIVOT_Z = "name => +__project.webgl.scene.watch.getObjectByName(name).position.z.toFixed(4)"
# Front (Housing <-> dial layer) minus back (Backplate <-> rotor layer), for WHOOP and the hidden watch.
SPREAD = """() => {
  const w = __project.webgl.scene.watch, z = n => w.getObjectByName(n).position.z;
  return {whoop: z('Housing_Pivot') - z('Backplate_Pivot'), watch: z('xploded-45') - z('xploded-9'),
          progress: __project.webgl.scene.xplodAllProgress};
}"""


def wait_for_scroll(page):
    """The page eases its WebGL scroll; wait until it catches up."""
    for _ in range(80):
        page.wait_for_timeout(200)
        if page.evaluate("Math.abs(__project.webgl.sectionsController.currentScroll - scrollY) < 2"):
            break
    page.wait_for_timeout(600)


def check_interaction(page, label):
    """Hover and click a part in Disassembly, then long-press to explode all."""
    page.evaluate("""() => {
      const s = __project.webgl.sectionsController.sections.find(x => x.name === 'Disassembly');
      scrollTo(0, s.webglStart + (s.webglEnd - s.webglStart) * 0.6);
    }""")
    wait_for_scroll(page)
    # Parts are hoverable only between 45% and 80% of the section timeline.
    for _ in range(50):
        if page.evaluate(f"{DISASSEMBLY}.canHover"):
            break
        page.wait_for_timeout(200)
    # Let the layers finish easing apart before aiming at one.
    page.wait_for_timeout(1500)
    target = page.evaluate(f"""() => {{
      const s = {DISASSEMBLY};
      const part = s.watchParts.horizontal.find(p => p.name === 'xploded-29');
      const v = part.raycasterMesh.getWorldPosition(part.mesh.position.clone()).project(__project.webgl.camera);
      return {{x: (v.x + 1) / 2 * innerWidth, y: (1 - v.y) / 2 * innerHeight, canHover: s.canHover}};
    }}""")
    before = page.evaluate(PIVOT_Z, "Mainboard_Pivot")
    page.mouse.move(target["x"], target["y"], steps=8)
    page.wait_for_timeout(600)
    hovered = page.evaluate(f"{DISASSEMBLY}.hoveredIndex")
    page.mouse.down()
    page.mouse.up()
    page.wait_for_timeout(2600)
    page.screenshot(path=str(OUT / f"{label}-click-part.png"))
    clicked = page.evaluate(f"""() => {{
      const pivot = __project.webgl.scene.watch.getObjectByName('Mainboard_Pivot');
      return {{index: {DISASSEMBLY}.clickedIndex, z: +pivot.position.z.toFixed(4), ry: +pivot.rotation.y.toFixed(3)}};
    }}""")
    # Close the zoom the way the page's close button does, then hold to explode everything.
    page.evaluate(f"{DISASSEMBLY}.clickedIndex = null")
    page.wait_for_timeout(2200)
    page.mouse.move(target["x"] + 300, target["y"] - 250, steps=4)
    page.wait_for_timeout(300)
    rest = page.evaluate(SPREAD)
    page.mouse.down()
    # The page's long press has a 0.5 s delay and a 2 s ease; software GL runs
    # its timeline slowly, so hold until the page reports a full explode.
    for _ in range(60):
        page.wait_for_timeout(500)
        if page.evaluate("__project.webgl.scene.xplodAllProgress > 0.8"):
            break
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / f"{label}-longpress.png"))
    exploded = page.evaluate(SPREAD)
    page.mouse.up()
    page.wait_for_timeout(1500)
    return {"target": target, "mainboard_z_before": before, "hovered": hovered, "clicked": clicked, "rest": rest, "longpress": exploded}


server = subprocess.Popen([sys.executable, str(ROOT / "serve.py"), "--port", str(PORT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    time.sleep(1)
    reports = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--use-gl=angle", "--use-angle=swiftshader"])
        for label, width, height in (("desktop", 1440, 900), ("mobile", 390, 844)):
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            errors, failures, logs = [], [], []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda msg: logs.append(msg.text) if msg.type == "error" else None)
            page.on("response", lambda r: failures.append({"url": r.url, "status": r.status}) if r.status >= 400 else None)
            page.goto(f"http://127.0.0.1:{PORT}/", wait_until="domcontentloaded", timeout=90000)
            page.wait_for_selector("body.whoop-model-ready, body.whoop-model-failed", timeout=120000)
            page.wait_for_timeout(4500)
            page.evaluate(EXPOSE)
            shots = []
            steps = 24 if label == "desktop" else 12
            for i in range(steps + 1):
                page.evaluate(f"scrollTo(0, Math.round((document.documentElement.scrollHeight - innerHeight) * {i / steps}))")
                wait_for_scroll(page)
                name = f"{label}-{i:02d}.png"
                page.screenshot(path=str(OUT / name))
                shots.append({"shot": name, "scroll": page.evaluate("scrollY"), **page.evaluate(PROBE)})
            interaction = check_interaction(page, label) if label == "desktop" else None
            failures = [f for f in failures if KNOWN_MISSING not in f["url"]]
            logs = [line for line in logs if "404" not in line]
            reports.append({"viewport": label, "ready": page.evaluate("document.body.classList.contains('whoop-model-ready')"),
                            "errors": errors, "console_errors": logs, "http_errors": failures, "interaction": interaction, "shots": shots})
            page.close()
        browser.close()
    (OUT / "results.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    for report in reports:
        print(report["viewport"], "ready" if report["ready"] else "NOT READY", "errors:", report["errors"] + report["console_errors"], "http:", report["http_errors"])
        if report["interaction"]:
            print("  interaction:", json.dumps(report["interaction"]))
        for s in report["shots"]:
            housing = s["pivots"].get("Housing_Pivot", {})
            print(f"  {s['shot']} {s['section']} rot={s['watchRotation']} pos={s['watchPosition']} housing={housing} band={s['pivots'].get('Band_Pivot')} oldVisible={s['visibleWatchMeshes']}")
    for report in reports:
        assert report["ready"], report["viewport"]
        assert not report["errors"] and not report["console_errors"] and not report["http_errors"], report
        for s in report["shots"]:
            assert s["anchored"] and s["visibleWatchMeshes"] == 0 and s["footerWhoops"] == 4, s
        i = report["interaction"]
        if i:
            assert i["hovered"] is not None and i["clicked"]["index"] is not None, i
            assert i["clicked"]["z"] != i["mainboard_z_before"], i
            # The long press ran, and WHOOP layers moved exactly as the hidden watch layers did.
            rest, held = i["rest"], i["longpress"]
            assert held["progress"] > 0.8, i
            assert abs((held["whoop"] - rest["whoop"]) - (held["watch"] - rest["watch"])) < 1e-4, i
    print("OK")
finally:
    server.terminate()
    server.wait(timeout=10)
