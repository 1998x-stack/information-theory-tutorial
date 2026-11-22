#!/usr/bin/env python3
"""Build the checked-in static Pages artifact from src/. Python stdlib only."""
from __future__ import annotations
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def redirect(target: str, title: str, text: str) -> str:
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta http-equiv="refresh" content="0;url={target}">'
        f'<link rel="canonical" href="{target}"><title>{title}</title></head>'
        f'<body><p><a href="{target}">{text}</a></p></body></html>')

def entries():
    pairs = [
        ("src/home/index.html", "docs/index.html"),
        ("src/assets/site.css", "docs/assets/css/site.css"),
        ("src/assets/site.js", "docs/assets/js/site.js"),
        ("src/assets/legacy.css", "docs/chapters/theme.css"),
        ("src/data/courses.json", "docs/data/courses.json"),
    ]
    for source, dest in pairs:
        yield dest, (ROOT / source).read_text(encoding="utf-8")
    for filename in sorted((ROOT / "src/figures").glob("*.svg")):
        yield "docs/assets/figures/" + filename.name, filename.read_text(encoding="utf-8")
    for n in range(1, 29):
        nn = f"{n:02d}"
        chapter = (ROOT / f"src/chapters/{nn}.html").read_text(encoding="utf-8")
        yield f"docs/chapters/{nn}.html", chapter
        dest = f"docs/chapters/{nn}.html"
        yield f"{nn}.html", redirect(dest, "章节已迁移", f"前往第 {nn} 章")
    yield "index.html", redirect("docs/index.html", "信息论课程首页", "打开信息论课程首页")
    yield "docs/chapters/index.html", ('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=../index.html"><title>返回课程首页</title><a href="../index.html">返回课程首页</a>')
    yield ".nojekyll", ""
    yield "docs/.nojekyll", ""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if tracked Pages output is stale")
    args = parser.parse_args()
    stale = []
    total = 0
    for target, content in entries():
        total += 1
        path = ROOT / target
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            stale.append(target)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
    if args.check and stale:
        print("Stale or missing generated paths:\\n" + "\\n".join(stale))
        raise SystemExit(1)
    print(f"Checked {total} generated files: " + ("clean" if not stale else f"updated {len(stale)}"))

if __name__ == "__main__":
    main()
