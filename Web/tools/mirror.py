"""Download the public FS 60P frontend into a self-contained local site."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
from html import unescape
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import json
import re

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
CAPTURE = PROJECT / "outputs" / "thewatch_20261009_035645"
SITE = ROOT / "site"
ORIGIN = "https://thewatch.60fps.fr"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"


def get(url: str) -> tuple[bytes, str]:
    with urlopen(Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}), timeout=90) as response:
        return response.read(), response.headers.get("Content-Type", "")


def destination(url: str) -> Path:
    parsed = urlsplit(url)
    if parsed.netloc == "thewatch.60fps.fr":
        relative = parsed.path.lstrip("/") or "index.html"
    elif parsed.netloc == "use.typekit.net":
        relative = "vendor/typekit/" + parsed.path.rsplit("/", 1)[-1]
    elif parsed.netloc == "p.typekit.net":
        relative = "vendor/typekit/p.css"
    else:
        raise ValueError("Unexpected origin: " + url)
    target = (SITE / relative).resolve()
    if not target.is_relative_to(SITE.resolve()):
        raise ValueError("Path escaped site: " + url)
    return target


def asset_urls(text: str) -> set[str]:
    text = unescape(text)
    values = set(re.findall(r"(?:/?assets/[\w./-]+\.(?:js|css|woff2?|ttf|png|jpe?g|webp|svg|glb|exr|mp4|mp3))", text))
    return {ORIGIN + "/" + value.lstrip("/") for value in values}


def download(url: str) -> dict:
    target = destination(url)
    try:
        body, mime = get(url)
        if target.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg", ".glb", ".exr", ".woff", ".woff2", ".ttf"} and "text/html" in mime.lower():
            raise ValueError("Server returned HTML instead of asset")
        if target.suffix == ".css" and target.name == "index-BDKORhKJ.css":
            body = body.replace(b"https://use.typekit.net/qgk0diq.css", b"/vendor/typekit/qgk0diq.css")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        return {"url": url, "file": target.relative_to(SITE).as_posix(), "bytes": len(body), "content_type": mime, "sha256": sha256(body).hexdigest()}
    except Exception as exc:
        return {"url": url, "error": str(exc)}


def main() -> None:
    current_entry = SITE / "index.html"
    if current_entry.exists() and "whoop-overlay.js" in current_entry.read_text("utf-8", errors="ignore"):
        raise SystemExit("The FS 60P page already contains the WHOOP model overlay; mirror will not overwrite it.")
    SITE.mkdir(parents=True, exist_ok=True)
    raw_html = next((CAPTURE / "responses/html").glob("*.html")).read_text("utf-8")
    raw_html = re.sub(r'<script type="module" src="https://static\.cloudflareinsights\.com/.*?</script>', "", raw_html, flags=re.S)
    raw_html = re.sub(r'<script>window\.__CF\$cv\$params=.*?</script>', "", raw_html, flags=re.S)
    raw_html = raw_html.replace("https://thewatch.60fps.fr/share-image.webp", "/share-image.webp")
    (SITE / "index.html").write_text(raw_html, encoding="utf-8")

    responses = json.loads((CAPTURE / "network/responses.json").read_text("utf-8"))
    urls = {entry["url"] for entry in responses if entry["url"].startswith(ORIGIN + "/assets/") and "?" not in entry["url"]}
    urls.update({ORIGIN + "/favicon.png", ORIGIN + "/share-image.webp"})
    urls.add("https://use.typekit.net/qgk0diq.css")
    for item in (CAPTURE / "responses").rglob("*"):
        if item.suffix in {".js", ".css", ".html"}:
            urls.update(asset_urls(item.read_text("utf-8", errors="replace")))
    # Parts are assembled from names at runtime, so they are not all literal URLs.
    for name in ("dial", "hands", "crystal", "bezel", "lugs", "strap", "buckle", "crown", "caseback", "movement"):
        urls.add(f"{ORIGIN}/assets/the-watch/img/parts/{name}.jpg")

    records = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(download, url): url for url in sorted(urls)}
        for future in as_completed(futures):
            record = future.result()
            records.append(record)
            print(("OK " if "file" in record else "MISS ") + record["url"] + (" " + record.get("error", "")), flush=True)

    typekit_css = SITE / "vendor/typekit/qgk0diq.css"
    if typekit_css.exists():
        css = typekit_css.read_text("utf-8")
        css = re.sub(r'@import url\("https://p\.typekit\.net/p\.css[^\n]+\n', "", css)
        for index, url in enumerate(re.findall(r'url\("(https://use\.typekit\.net/af/[^\"]+/l\?[^\"]+)"\) format\("woff2"\)', css)):
            try:
                body, mime = get(url)
                name = f"freight-big-pro-{index}.woff2"
                target = SITE / "vendor/typekit" / name
                target.write_bytes(body)
                records.append({"url": url, "file": target.relative_to(SITE).as_posix(), "bytes": len(body), "content_type": mime, "sha256": sha256(body).hexdigest()})
                css = re.sub(r'src:url\("' + re.escape(url) + r'"\) format\("woff2"\),url\([^;]+;', f'src:url("/vendor/typekit/{name}") format("woff2");', css)
            except Exception as exc:
                records.append({"url": url, "error": str(exc)})
        typekit_css.write_text(css, encoding="utf-8")

    manifest = sorted(records, key=lambda entry: entry["url"])
    (ROOT / "asset-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Downloaded {sum('file' in item for item in manifest)}/{len(manifest)} assets", flush=True)


if __name__ == "__main__":
    main()
