#!/usr/bin/env python3
"""Checks the site before publishing:  python3 tools/check.py

- every HTML page parses as valid HTML5 (html5lib in strict mode, if installed; stdlib checks otherwise)
- one <h1>, no skipped heading levels, unique ids, lang on <html>, a <title> and a description
- every <img> has an alt attribute
- every internal link and #anchor points to a file and an id that exist (including sitemap.xml entries)
- no page loads anything from another site (scripts, styles, images, fonts, frames)

Exits non-zero on any problem. Standard library only, plus html5lib when available.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://raicita.thymoria.com"
SKIP_DIRS = {".git", "tools", "node_modules"}

try:
    import html5lib  # type: ignore
except ImportError:  # pragma: no cover
    html5lib = None


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.links: list[tuple[str, str]] = []  # (tag, url)
        self.loads: list[tuple[str, str]] = []  # resources the browser fetches
        self.headings: list[int] = []
        self.imgs_without_alt = 0
        self.html_lang = None
        self.title = False
        self.description = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "html":
            self.html_lang = a.get("lang")
        if tag == "title":
            self.title = True
        if tag == "meta" and a.get("name") == "description" and a.get("content"):
            self.description = True
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if tag == "a" and a.get("href"):
            self.links.append((tag, a["href"]))
        if tag == "img":
            if "alt" not in a:
                self.imgs_without_alt += 1
            self.loads.append((tag, a.get("src", "")))
        if tag in ("script", "iframe", "source", "video", "audio") and a.get("src"):
            self.loads.append((tag, a["src"]))
        if tag == "link" and a.get("href"):
            rel = a.get("rel", "")
            if rel in ("canonical", "alternate"):
                self.links.append(("link-meta", a["href"]))
            else:
                self.loads.append(("link", a["href"]))

    handle_startendtag = handle_starttag


def pages() -> list[Path]:
    return sorted(p for p in ROOT.rglob("*.html") if not (set(p.relative_to(ROOT).parts) & SKIP_DIRS))


def resolve(base: Path, url: str) -> tuple[Path | None, str]:
    """Local file a link points to (None for external/mailto/tel) and its fragment."""
    parts = urlsplit(url)
    if parts.scheme in ("mailto", "tel", "sms"):
        return None, ""
    if parts.scheme in ("http", "https"):
        if url.startswith(SITE):
            path = parts.path or "/"
            target = ROOT / path.lstrip("/")
        else:
            return None, ""
    elif parts.path.startswith("/"):
        target = ROOT / unquote(parts.path).lstrip("/")
    elif parts.path == "":
        target = base
    else:
        target = (base.parent / unquote(parts.path)).resolve()
    if target.is_dir() or str(url).endswith("/") and parts.path:
        target = target / "index.html"
    return target, parts.fragment


def main() -> int:
    problems: list[str] = []
    parsed: dict[Path, Page] = {}
    for f in pages():
        text = f.read_text(encoding="utf-8")
        rel = f.relative_to(ROOT)
        if html5lib is not None:
            parser = html5lib.HTMLParser(strict=True)
            try:
                parser.parse(text)
            except Exception as e:  # noqa: BLE001
                problems.append(f"{rel}: invalid HTML: {e}")
        p = Page()
        p.feed(text)
        parsed[f] = p
        if not text.lstrip().lower().startswith("<!doctype html>"):
            problems.append(f"{rel}: missing <!doctype html> at the top")
        if not p.html_lang:
            problems.append(f"{rel}: <html> has no lang")
        if not p.title:
            problems.append(f"{rel}: no <title>")
        if not p.description and rel.name != "404.html" and "tools" not in rel.parts:
            problems.append(f"{rel}: no meta description")
        if p.headings.count(1) != 1:
            problems.append(f"{rel}: {p.headings.count(1)} <h1> elements (want 1)")
        for prev, cur in zip(p.headings, p.headings[1:]):
            if cur > prev + 1:
                problems.append(f"{rel}: heading jumps from h{prev} to h{cur}")
                break
        dup = {i for i in p.ids if p.ids.count(i) > 1}
        if dup:
            problems.append(f"{rel}: duplicate ids {sorted(dup)}")
        if p.imgs_without_alt:
            problems.append(f"{rel}: {p.imgs_without_alt} <img> without alt")
        for tag, url in p.loads:
            if urlsplit(url).scheme in ("http", "https") or url.startswith("//"):
                problems.append(f"{rel}: loads an external resource <{tag}> {url}")

    checked = 0
    for f, p in parsed.items():
        rel = f.relative_to(ROOT)
        for tag, url in p.links + p.loads:
            target, frag = resolve(f, url)
            if target is None:
                continue
            checked += 1
            if not target.exists():
                problems.append(f"{rel}: broken link {url} -> {target.relative_to(ROOT) if target.is_relative_to(ROOT) else target}")
                continue
            if frag and target.suffix == ".html":
                tp = parsed.get(target)
                if tp is None:
                    tp = Page()
                    tp.feed(target.read_text(encoding="utf-8"))
                if frag not in tp.ids:
                    problems.append(f"{rel}: missing anchor {url}")

    sm = ROOT / "sitemap.xml"
    if sm.exists():
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for loc in ET.parse(sm).getroot().findall(".//s:loc", ns):
            target, _ = resolve(ROOT / "index.html", loc.text or "")
            checked += 1
            if target is None or not target.exists():
                problems.append(f"sitemap.xml: {loc.text} has no page")

    for line in problems:
        print("FAIL", line)
    print(f"check: {len(parsed)} pages, {checked} internal links and resources checked, {len(problems)} problem(s)"
          + ("" if html5lib else " (html5lib not installed: HTML validity not checked)"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
