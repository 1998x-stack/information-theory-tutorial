#!/usr/bin/env python3
"""Static link, MathML, chapter, and SVG checks; not browser QA."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

class Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.tags = {}
    def handle_starttag(self, tag, attrs):
        self.tags[tag] = self.tags.get(tag, 0) + 1
        a = dict(attrs)
        if tag in ("a", "img", "script", "link"):
            url = a.get("href") or a.get("src")
            if url:
                self.links.append(url)

def validate():
    errors = []
    names = [DOCS / "index.html"] + [DOCS / f"chapters/{n:02d}.html" for n in range(1,29)]
    for page in names:
        if not page.is_file():
            errors.append(f"Missing: {page}")
            continue
        content = page.read_text(encoding="utf-8")
        scan = Scan()
        scan.feed(content)
        if not content.lower().startswith("<!doctype html>"):
            errors.append(f"Doctype: {page}")
        for url in scan.links:
            parsed = urlsplit(url)
            if parsed.scheme or url.startswith("//") or url.startswith("#") or url.startswith("mailto:"):
                continue
            local = (page.parent / parsed.path).resolve() if parsed.path else page
            if not local.is_file():
                errors.append(f"Broken {page.relative_to(ROOT)} -> {url}")
        if page.name in {f"{i:02d}.html" for i in range(1,29)}:
            minimum_figures = 4 if int(page.stem) >= 26 else (3 if int(page.stem) >= 6 else 2)
            if scan.tags.get("h1",0) != 1 or scan.tags.get("math",0) < 1 or scan.tags.get("figure",0) < minimum_figures:
                errors.append(f"New chapter semantic tags: {page}")
            if not all(token in content for token in ('class="math-scroll"', 'aria-label=', 'id="sources"', 'data-lab=', 'aria-live="polite"')):
                errors.append(f"New chapter math/reference a11y: {page}")
    for figure in sorted((DOCS / "assets/figures").glob("*.svg")):
        try:
            root = ET.parse(figure).getroot()
            if not root.tag.endswith("svg") or "viewBox" not in root.attrib:
                errors.append(f"SVG sizing: {figure}")
            if not any(c.tag.endswith("title") for c in root) or not any(c.tag.endswith("desc") for c in root):
                errors.append(f"SVG a11y: {figure}")
        except ET.ParseError as e:
            errors.append(f"SVG parse: {figure}: {e}")
    if len(list((DOCS / "assets/figures").glob("*.svg"))) < 88:
        errors.append("Expected at least eighty-eight original SVG diagrams")
    data = json.loads((DOCS / "data/courses.json").read_text(encoding="utf-8"))
    if data.get("chapterCount") != 28 or len(data.get("chapters", [])) != 28:
        errors.append("Course metadata inconsistent with 28 chapters")
    if errors:
        print("\\n".join(errors))
        raise SystemExit(1)
    print(f"Static validation passed: {len(names)} HTML, 88+ SVG, local links and semantic checks")
if __name__ == "__main__":
    validate()
