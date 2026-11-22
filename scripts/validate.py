#!/usr/bin/env python3
"""Static integrity checks for the published course; browser behavior is tested separately."""
from __future__ import annotations

from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CHAPTERS = [DOCS / "chapters" / f"{n:02d}.html" for n in range(1, 29)]
PAGES = [DOCS / "index.html", *CHAPTERS]
EXPECTED_MATH_CHILDREN = {
    "mfrac": 2, "mroot": 2, "msub": 2, "msup": 2,
    "munder": 2, "mover": 2, "msubsup": 3, "munderover": 3,
}


class Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = set()
        self.duplicate_ids = []
        self.tags = Counter()
        self.images = []
        self.figure_captions = []
        self._figure_stack = []
        self._in_title = False
        self.title_text = []

    def handle_starttag(self, tag, attrs):
        self.tags[tag] += 1
        attrs = dict(attrs)
        if attrs.get("id"):
            value = attrs["id"]
            if value in self.ids:
                self.duplicate_ids.append(value)
            self.ids.add(value)
        if tag in ("a", "img", "script", "link"):
            url = attrs.get("href") or attrs.get("src")
            if url:
                self.links.append(url)
        if tag == "img":
            self.images.append(attrs)
        if tag == "figure":
            self._figure_stack.append(False)
        if tag == "figcaption" and self._figure_stack:
            self._figure_stack[-1] = True
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "figure" and self._figure_stack:
            self.figure_captions.append(self._figure_stack.pop())
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title_text.append(data)


def fail(errors, page, message):
    errors.append(f"{page.relative_to(ROOT)}: {message}")


def scan_page(page, cache):
    if page not in cache:
        parser = Scan()
        parser.feed(page.read_text(encoding="utf-8"))
        cache[page] = parser
    return cache[page]


def validate_mathml(page, content, errors):
    formulas = list(re.finditer(r"<math\b([^>]*)>([\s\S]*?)</math>", content, re.I))
    wrappers = list(re.finditer(r"<div\b[^>]*class=\"math-scroll\"[^>]*>", content, re.I))
    if len(formulas) != len(wrappers):
        fail(errors, page, f"MathML wrappers {len(wrappers)} != formulas {len(formulas)}")
    for index, match in enumerate(formulas, 1):
        attrs, body = match.groups()
        if not re.search(r"\baria-label\s*=\s*\"", attrs, re.I):
            fail(errors, page, f"MathML #{index} missing its own aria-label")
        try:
            root = ET.fromstring("<math>" + body + "</math>")
        except ET.ParseError as exc:
            fail(errors, page, f"MathML #{index} is not well-formed XML: {exc}")
            continue
        for node in root.iter():
            tag = node.tag.rsplit("}", 1)[-1].lower()
            children = list(node)
            if tag in EXPECTED_MATH_CHILDREN and len(children) != EXPECTED_MATH_CHILDREN[tag]:
                fail(errors, page, f"MathML #{index}: {tag} has {len(children)} children, expected {EXPECTED_MATH_CHILDREN[tag]}")
            if tag in {"mrow", "mtable", "mtr", "mtd"} and not children:
                fail(errors, page, f"MathML #{index}: empty {tag}")
            if tag in {"mi", "mn", "mo", "mtext"} and not children and not (node.text or "").strip():
                fail(errors, page, f"MathML #{index}: empty {tag}")
            if tag == "mfenced":
                fail(errors, page, f"MathML #{index}: mfenced is not part of MathML Core; use explicit mrow/mo brackets")


def validate_local_links(page, parser, cache, errors):
    for url in parser.links:
        parsed = urlsplit(url)
        if parsed.scheme or url.startswith("//"):
            continue
        if url.startswith(("mailto:", "tel:", "data:", "javascript:")):
            continue
        local = (page.parent / unquote(parsed.path)).resolve() if parsed.path else page.resolve()
        if not local.is_file():
            fail(errors, page, f"broken local reference {url}")
            continue
        if parsed.fragment and local.suffix.lower() in {".html", ".htm"}:
            target = scan_page(local, cache)
            fragment = unquote(parsed.fragment)
            if fragment not in target.ids:
                fail(errors, page, f"missing local fragment #{fragment} in {url}")


def validate_chapter(page, number, parser, content, errors):
    if parser.tags["h1"] != 1:
        fail(errors, page, f"expected exactly one h1, found {parser.tags['h1']}")
    if parser.tags["title"] != 1 or not "".join(parser.title_text).strip():
        fail(errors, page, "missing or empty document title")
    minimum_figures = 4 if number >= 26 else (3 if number >= 6 else 2)
    if parser.tags["math"] < 1 or parser.tags["figure"] < minimum_figures:
        fail(errors, page, f"missing required MathML/figures (math={parser.tags['math']}, figures={parser.tags['figure']})")
    if any(not image.get("alt", "").strip() for image in parser.images):
        fail(errors, page, "every image needs a meaningful non-empty alt attribute")
    if any(not caption for caption in parser.figure_captions):
        fail(errors, page, "every figure needs a figcaption")
    if parser.duplicate_ids:
        fail(errors, page, f"duplicate id values: {sorted(set(parser.duplicate_ids))}")
    if not re.search(r'class="math-scroll"[^>]*tabindex="0"[^>]*role="region"', content):
        fail(errors, page, "long-formula region must be keyboard focusable and named")
    bad_tokens = ("oplus", "R&amp;lt;C", "&amp;lt;", "&amp;gt;", "TODO", "FIXME", "Lorem ipsum", "讲义介绍了")
    for token in bad_tokens:
        if token in content:
            fail(errors, page, f"unresolved editorial/notation artifact {token!r}")


def validate_navigation(number, page, content, errors):
    match = re.search(r'<nav class="chapter-nav"[^>]*>([\s\S]*?)</nav>', content, re.I)
    if not match:
        fail(errors, page, "missing adjacent-chapter navigation")
        return
    hrefs = re.findall(r'<a\b[^>]*href="([^"]+)"', match.group(1), re.I)
    if len(hrefs) < 2:
        fail(errors, page, "adjacent navigation needs previous and next links")
        return
    expected_previous = "../index.html" if number == 1 else f"{number - 1:02d}.html"
    expected_next = "../index.html" if number == 28 else f"{number + 1:02d}.html"
    if hrefs[0] != expected_previous or hrefs[-1] != expected_next:
        fail(errors, page, f"navigation expected ({expected_previous}, {expected_next}), found ({hrefs[0]}, {hrefs[-1]})")


def validate_labs(chapters, site_js, errors):
    handlers = set(re.findall(r'case "([^"]+)"\s*:', site_js))
    seen = set()
    for page in chapters:
        content = page.read_text(encoding="utf-8")
        for match in re.finditer(r'<div class="lab" data-lab="([^"]+)"[^>]*>([\s\S]*?)</div>', content, re.I):
            lab_id, body = match.groups()
            if lab_id in seen:
                fail(errors, page, f"duplicate interactive lab id {lab_id}")
            seen.add(lab_id)
            if lab_id not in handlers:
                fail(errors, page, f"no site.js handler for lab {lab_id}")
            inputs = [dict(re.findall(r'([\w-]+)="([^"]*)"', item)) for item in re.findall(r"<input\b([^>]*)>", body, re.I)]
            sliders = [item for item in inputs if item.get("type") == "range"]
            if len(sliders) != 1:
                fail(errors, page, f"lab {lab_id} must have exactly one range control")
                continue
            control_id = sliders[0].get("id", "")
            if not control_id:
                fail(errors, page, f"lab {lab_id} range control has no id")
            if not re.search(r'<label\b[^>]*for="' + re.escape(control_id) + r'"', body, re.I):
                fail(errors, page, f"lab {lab_id} has no associated label")
            if not re.search(r'<output\b[^>]*aria-live="polite"', body, re.I):
                fail(errors, page, f"lab {lab_id} needs a polite live output")
    if len(handlers) != len(seen):
        missing = sorted(handlers - seen)
        if missing:
            errors.append("site.js has handlers without corresponding page labs: " + ", ".join(missing))


def validate_assets(errors):
    figure_dir = DOCS / "assets" / "figures"
    figures = sorted(figure_dir.glob("*.svg"))
    if len(figures) < 88:
        errors.append(f"expected at least 88 original SVG diagrams, found {len(figures)}")
    for figure in figures:
        try:
            root = ET.parse(figure).getroot()
            if not root.tag.endswith("svg") or "viewBox" not in root.attrib:
                errors.append(f"{figure.relative_to(ROOT)}: missing SVG root/viewBox")
            if not any(child.tag.endswith("title") for child in root):
                errors.append(f"{figure.relative_to(ROOT)}: missing direct-child title")
            if not any(child.tag.endswith("desc") for child in root):
                errors.append(f"{figure.relative_to(ROOT)}: missing direct-child desc")
        except ET.ParseError as exc:
            errors.append(f"{figure.relative_to(ROOT)}: SVG XML parse error: {exc}")


def validate_metadata(errors):
    course = json.loads((DOCS / "data" / "courses.json").read_text(encoding="utf-8"))
    if course.get("chapterCount") != 28 or len(course.get("chapters", [])) != 28:
        errors.append("course metadata is inconsistent with 28 chapters")
    evidence = json.loads((ROOT / "research" / "evidence.json").read_text(encoding="utf-8"))
    claims = evidence.get("claims", [])
    chapter_numbers = sorted(claim.get("chapter") for claim in claims)
    if chapter_numbers != list(range(1, 29)):
        errors.append("research/evidence.json must contain exactly one claim for each chapter 1–28")
    sources = evidence.get("sources", {})
    for claim in claims:
        for source in claim.get("evidence", []):
            if source not in sources:
                errors.append(f"evidence claim chapter {claim.get('chapter')} references missing source key {source}")


def validate():
    errors, cache = [], {}
    for page in PAGES:
        if not page.is_file():
            errors.append(f"missing published page: {page.relative_to(ROOT)}")
            continue
        content = page.read_text(encoding="utf-8")
        parser = scan_page(page, cache)
        if not content.lower().startswith("<!doctype html>"):
            fail(errors, page, "missing HTML5 doctype")
        validate_local_links(page, parser, cache, errors)
        if page == DOCS / "index.html":
            if parser.tags["h1"] != 1 or parser.tags["title"] != 1:
                fail(errors, page, "home page needs one h1 and one title")
        else:
            number = int(page.stem)
            validate_chapter(page, number, parser, content, errors)
            validate_navigation(number, page, content, errors)
            validate_mathml(page, content, errors)
    validate_labs(CHAPTERS, (ROOT / "src" / "assets" / "site.js").read_text(encoding="utf-8"), errors)
    validate_assets(errors)
    validate_metadata(errors)
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    math_count = sum(scan_page(page, cache).tags["math"] for page in CHAPTERS)
    svg_count = len(list((DOCS / "assets" / "figures").glob("*.svg")))
    print(f"Static validation passed: 29 HTML pages, 28 chapters, {math_count} MathML formulas, {svg_count} SVGs, local files/fragments, labs, navigation, evidence.")


if __name__ == "__main__":
    validate()
