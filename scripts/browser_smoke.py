#!/usr/bin/env python3
"""Offline Chromium checks for all course pages, MathML, diagrams, labs and print."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
VIEWPORTS = (1440, 768, 390, 360)
SCREENSHOT_PAGES = {
    "index.html", "chapters/06.html", "chapters/12.html", "chapters/15.html",
    "chapters/19.html", "chapters/22.html", "chapters/25.html", "chapters/27.html",
    "chapters/28.html",
}
PRINT_PAGES = (1, 12, 15, 19, 25, 27, 28)


def verify(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    failures, records = [], []
    filenames = ["index.html"] + [f"chapters/{n:02d}.html" for n in range(1, 29)]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for width in VIEWPORTS:
            context = browser.new_context(
                viewport={"width": width, "height": 900},
                device_scale_factor=1,
            )
            for name in filenames:
                page = context.new_page()
                runtime_errors, console_errors, external_requests = [], [], []
                page.on("pageerror", lambda exc: runtime_errors.append(str(exc)))
                page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
                page.on("request", lambda req: external_requests.append(req.url)
                        if req.url.startswith(("http://", "https://")) else None)
                try:
                    page.goto((DOCS / name).resolve().as_uri(), wait_until="load", timeout=15000)
                    page.evaluate("() => document.querySelectorAll('figure img').forEach(img => { img.loading = 'eager'; })")
                    page.wait_for_function(
                        "() => [...document.querySelectorAll('figure img')].every(img => img.complete)",
                        timeout=8000,
                    )
                    state = page.evaluate("""() => {
                        const math = [...document.querySelectorAll('math')];
                        const fractions = [...document.querySelectorAll('mfrac')];
                        const limits = [...document.querySelectorAll('munder,mover,munderover')];
                        const images = [...document.querySelectorAll('figure img')];
                        const scrolls = [...document.querySelectorAll('.math-scroll')];
                        const rect = el => el.getBoundingClientRect();
                        return {
                            title: document.title.trim(),
                            h1Count: document.querySelectorAll('h1').length,
                            overflow: document.documentElement.scrollWidth - innerWidth,
                            figureCount: document.querySelectorAll('figure').length,
                            brokenImages: images.filter(img => !img.complete || img.naturalWidth <= 0).map(img => img.src),
                            math: math.map(el => ({
                                namespace: el.namespaceURI,
                                label: !!el.getAttribute('aria-label'),
                                width: rect(el).width,
                                height: rect(el).height,
                                scrollRegion: !!el.closest('.math-scroll') &&
                                    el.closest('.math-scroll').getAttribute('tabindex') === '0' &&
                                    el.closest('.math-scroll').getAttribute('role') === 'region'
                            })),
                            fractions: fractions.map(el => {
                                const numerator = el.children[0] && rect(el.children[0]);
                                const denominator = el.children[1] && rect(el.children[1]);
                                return !!(numerator && denominator && numerator.height > 0 &&
                                    denominator.height > 0 && numerator.top < denominator.top);
                            }),
                            limits: limits.map(el => {
                                const expected = el.tagName.toLowerCase() === 'munderover' ? 3 : 2;
                                return el.children.length === expected &&
                                    [...el.children].every(child => rect(child).width > 0 && rect(child).height > 0);
                            }),
                            unsupportedMfenced: document.querySelectorAll('mfenced').length,
                            sliders: [...document.querySelectorAll('.lab input[type="range"]')].map(el => {
                                const lab = el.closest('.lab');
                                const output = lab && lab.querySelector('output');
                                const label = el.id && document.querySelector('label[for="' + el.id + '"]');
                                return {id: el.id, hasLabel: !!label, hasOutput: !!output,
                                    live: !!output && output.getAttribute('aria-live') === 'polite',
                                    value: el.value, outputText: output ? output.textContent.trim() : ''};
                            })
                        };
                    }""")
                    faults = []
                    if not state["title"] or state["h1Count"] != 1:
                        faults.append("document title or h1 missing")
                    if state["overflow"] > 1:
                        offenders = page.evaluate("""() => [...document.querySelectorAll('body *')]
                            .filter(el => el.getBoundingClientRect().right > innerWidth + 1 &&
                                !el.closest('figure') && !el.closest('.math-scroll') &&
                                !el.closest('.table-scroll') && !el.closest('pre'))
                            .slice(0, 10).map(el => ({
                                tag: el.tagName, cls: el.className?.baseVal || el.className || '',
                                right: Math.round(el.getBoundingClientRect().right),
                                left: Math.round(el.getBoundingClientRect().left)
                            }))""")
                        faults.append(f"horizontal overflow {state['overflow']}px; offenders={offenders}")
                    if state["brokenImages"]:
                        faults.append("unloaded figures: " + str(state["brokenImages"]))
                    if external_requests:
                        faults.append("external runtime requests in offline build: " + str(external_requests))
                    if state["unsupportedMfenced"]:
                        faults.append("legacy mfenced element is not permitted")
                    if name != "index.html":
                        number = int(Path(name).stem)
                        minimum = 4 if number >= 26 else (3 if number >= 6 else 2)
                        if state["figureCount"] < minimum:
                            faults.append(f"figures {state['figureCount']} < {minimum}")
                        if not state["math"] or any(
                            item["namespace"] != "http://www.w3.org/1998/Math/MathML" or
                            not item["label"] or item["width"] <= 0 or item["height"] <= 0 or
                            not item["scrollRegion"] for item in state["math"]
                        ):
                            faults.append("MathML namespace, accessible label, scroll region or geometry")
                        if not all(state["fractions"]):
                            faults.append("MathML stacked fraction geometry")
                        if not all(state["limits"]):
                            faults.append("MathML sum/limit geometry")
                        for index, slider in enumerate(state["sliders"], 1):
                            if not slider["id"] or not slider["hasLabel"] or not slider["hasOutput"] or not slider["live"]:
                                faults.append(f"range control {index} lacks accessible label/live output")
                        sliders = page.locator(".lab input[type='range']")
                        for index in range(sliders.count()):
                            slider = sliders.nth(index)
                            output = slider.locator("xpath=..").locator("output").first
                            before = output.inner_text()
                            slider.focus()
                            slider.press("ArrowRight")
                            after = output.inner_text()
                            if not before or before == after:
                                faults.append(f"keyboard range control {index + 1} did not update output")
                    if runtime_errors:
                        faults.append("JavaScript page errors: " + " | ".join(runtime_errors))
                    if console_errors:
                        faults.append("console errors: " + " | ".join(console_errors))
                    if width in (1440, 390) and name in SCREENSHOT_PAGES:
                        page.screenshot(
                            path=str(output / f"{Path(name).stem}-{width}.png"),
                            full_page=True,
                            animations="disabled",
                        )
                    records.append({
                        "path": name, "viewport": width, "passed": not faults,
                        "mathCount": len(state["math"]), "figureCount": state["figureCount"],
                        "sliderCount": len(state["sliders"]), "issues": faults,
                    })
                    if faults:
                        failures.append(f"{name}@{width}: " + "; ".join(faults))
                except Exception as exc:
                    failures.append(f"{name}@{width}: {exc}")
                    records.append({"path": name, "viewport": width, "passed": False, "issues": [str(exc)]})
                finally:
                    page.close()
            context.close()

        print_records = []
        for number in PRINT_PAGES:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            try:
                page.goto((DOCS / "chapters" / f"{number:02d}.html").resolve().as_uri(), wait_until="load")
                page.evaluate("() => document.querySelectorAll('figure img').forEach(img => { img.loading = 'eager'; })")
                page.wait_for_function(
                    "() => [...document.querySelectorAll('figure img')].every(img => img.complete)",
                    timeout=8000,
                )
                page.emulate_media(media="print")
                visible = page.evaluate("""() => ({
                    math: [...document.querySelectorAll('math')].every(el => {
                        const r = el.getBoundingClientRect();
                        return r.width > 0 && r.height > 0;
                    }),
                    figures: [...document.querySelectorAll('figure img')].every(img => img.naturalWidth > 0)
                })""")
                passed = visible["math"] and visible["figures"]
                print_records.append({"chapter": number, "passed": passed, **visible})
                if not passed:
                    failures.append(f"print mode chapter {number}: {visible}")
            finally:
                page.close()
        browser.close()

    report = {
        "browser": "Chromium",
        "viewports": list(VIEWPORTS),
        "records": records,
        "printRecords": print_records,
        "passed": not failures,
        "failures": failures,
    }
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if failures:
        print("\n".join(failures))
        raise SystemExit(1)
    print(f"Browser QA passed: {len(records)} page/viewport checks, {len(print_records)} print checks.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="reports/browser")
    args = parser.parse_args()
    verify(Path(args.output))
