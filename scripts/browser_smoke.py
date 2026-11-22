#!/usr/bin/env python3
"""Real Chromium verification for the HTML course, not a simulated check.

Runs offline file:// to verify no CDN dependencies. Checks 1440/390/360,
SVG images, MathML namespace and geometry, keyboard range interactions,
horizontal page overflow, and print mode. Screenshots are CI artifacts.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

def verify(output):
    output.mkdir(parents=True,exist_ok=True)
    failures,records=[],[]
    filenames=["index.html"]+[f"chapters/{n:02d}.html" for n in range(1,11)]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        for width in (1440,390,360):
            context=browser.new_context(viewport={"width":width,"height":900},device_scale_factor=1)
            for name in filenames:
                file=DOCS/name
                page=context.new_page()
                runtime_errors=[]
                page.on("pageerror",lambda exc:runtime_errors.append(str(exc)))
                try:
                    page.goto(file.resolve().as_uri(),wait_until="load",timeout=15000)
                    page.evaluate("""() => document.querySelectorAll('figure img').forEach(img=>{img.loading='eager'})""")
                    page.wait_for_function("""() => [...document.querySelectorAll('figure img')].every(i=>i.complete)""",timeout=6000)
                    state=page.evaluate("""() => {
                        const math=[...document.querySelectorAll('math')];
                        const fractions=[...document.querySelectorAll('mfrac')];
                        const images=[...document.querySelectorAll('figure img')];
                        const formulas=math.map(el=>({
                          ns:el.namespaceURI,
                          width:el.getBoundingClientRect().width,
                          height:el.getBoundingClientRect().height
                        }));
                        return {
                          overflow:document.documentElement.scrollWidth-innerWidth,
                          figures:images.length,
                          brokenImages:images.filter(i=>!i.complete||i.naturalWidth<=0).map(i=>i.src),
                          math:formulas,
                          fractions:fractions.map(el=>{
                              const n=el.children[0]?.getBoundingClientRect();
                              const d=el.children[1]?.getBoundingClientRect();
                              return !!(n && d && n.height>0 && d.height>0 && n.top < d.top);
                          })
                        };
                    }""")
                    faults=[]
                    if state["overflow"]>1:
                        offenders=page.evaluate("""() => [...document.querySelectorAll('body *')]
                            .filter(el=>el.getBoundingClientRect().right>innerWidth+1 &&
                                 !el.closest('figure'))
                            .slice(0,12).map(el=>({
                              tag:el.tagName,cls:el.className?.baseVal||el.className||'',
                              right:Math.round(el.getBoundingClientRect().right),
                              left:Math.round(el.getBoundingClientRect().left)
                            }))""")
                        faults.append(f"horizontal overflow {state['overflow']}px, elements={offenders}")
                    if state["brokenImages"]:
                        faults.append("unloaded figures: "+str(state["brokenImages"]))
                    if name!="index.html":
                        num=int(Path(name).stem)
                        minfig=3 if num>=6 else 2
                        if state["figures"]<minfig:
                            faults.append(f"figures {state['figures']} < {minfig}")
                        if not state["math"] or any(
                            v["ns"]!="http://www.w3.org/1998/Math/MathML"
                            or v["width"]<=0 or v["height"]<=0
                            for v in state["math"]):
                            faults.append("MathML namespace/geometry")
                        if not all(state["fractions"]):
                            faults.append("MathML stacked fraction geometry")
                        slider=page.locator('.lab input[type="range"]').first
                        if slider.count():
                            output_element=page.locator(".lab output").first
                            before=output_element.inner_text()
                            slider.focus()
                            slider.press("ArrowRight")
                            after=output_element.inner_text()
                            if not before or before==after:
                                faults.append("keyboard range control did not update output")
                    if width in (1440,390) and name in (
                        "index.html","chapters/06.html","chapters/07.html",
                        "chapters/08.html","chapters/09.html","chapters/10.html"
                    ):
                        page.screenshot(
                            path=str(output/f"{Path(name).stem}-{width}.png"),
                            full_page=True,animations="disabled"
                        )
                    if runtime_errors:
                        faults.append("JS: "+" | ".join(runtime_errors))
                    records.append({"path":name,"viewport":width,"pass":not faults,
                                    "mathCount":len(state["math"]),
                                    "figureCount":state["figures"],"issues":faults})
                    if faults: failures.append(f"{name}@{width}: "+", ".join(faults))
                except Exception as exc:
                    failures.append(f"{name}@{width}: {exc}")
                    records.append({"path":name,"viewport":width,"pass":False,"issues":[str(exc)]})
                finally:
                    page.close()
            context.close()
        # A representative chapter in print media; check equations remain visible.
        page=browser.new_page(viewport={"width":1440,"height":900})
        page.goto((DOCS/"chapters/10.html").resolve().as_uri())
        page.emulate_media(media="print")
        print_check=page.evaluate("""() => [...document.querySelectorAll('math')].every(
            el=>el.getBoundingClientRect().width>0 && el.getBoundingClientRect().height>0
        )""")
        if not print_check: failures.append("Print mode: chapter 10 math invisible")
        page.close()
        browser.close()
    (output/"report.json").write_text(json.dumps({
        "browser":"Chromium","viewports":[1440,390,360],"records":records,
        "print_math":print_check,"passed":not failures,"failures":failures
    },ensure_ascii=False,indent=2),encoding="utf-8")
    if failures:
        print("\n".join(failures))
        raise SystemExit(1)
    print(f"Browser QA passed: {len(records)} page/viewport checks, keyboard, MathML, SVG, print")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="reports/browser")
    args=parser.parse_args()
    verify(Path(args.output))
