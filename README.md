# 信息论 · 从概率到通信极限

[课程首页（GitHub Pages）](https://1998x-stack.github.io/information-theory-tutorial/) · [源码仓库](https://github.com/1998x-stack/information-theory-tutorial)

28 章中文信息论教程，从概率、熵、互信息走到压缩、可靠通信、统计学习和信息瓶颈。**01–05 章已进行首批深度精修；06–28 保留原版，待后续逐章审核。**

## 本地阅读与构建

```bash
python3 scripts/build.py
python3 scripts/build.py --check
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 -m http.server 8000     # http://localhost:8000/docs/
```

无需 Node.js 或 CDN，静态 HTML 在现代浏览器中无需网络即可阅读。站外参考链接需要联网。

## 结构

```text
src/
  home/index.html         # 首页可维护源文件
  chapters/01.html…28.html
  data/courses.json
  assets/site.css, site.js, legacy.css
  figures/*.svg            # 独立的原绘信息论图解
docs/                    # GitHub Pages 可直接读取的静态发布产物
  index.html
  chapters/01.html…28.html
  chapters/theme.css      # 旧版 06–28 的样式兼容层
  assets/css, assets/js, assets/figures
scripts/build.py          # 构建 & --check 一致性校验
scripts/validate.py       # 链接、SVG 和基本 HTML 验收
examples/foundations.py   # 离散信息量计算样例
tests/                    # 数值断言
research/evidence.json    # 关键论断的来源
AGENTS.md                 # 章节维护规范
```

根目录的 `01.html`…`28.html` 与 `index.html` 保留兼容跳转到 `docs/`。既有 Pages 使用仓库根目录时无需改源设置；若配置为 `/docs` 则直接使用 `docs/index.html`。实际 Pages 是否发布成功须在部署后验证。

## 编辑规范

按 [AGENTS.md](AGENTS.md) 中的逐篇流程维护文章。所有数学式明确基底、支持集和零概率约定；优先使用离线原生 MathML；SVG 要有独立标题、描述和图注，移动端阅读、键盘操作和屏幕阅读器均需验收。

资料与方法参考：Shannon (1948)、Cover & Thomas (2006)、[MIT 6.441](https://ocw.mit.edu/courses/6-441-information-theory-spring-2010/pages/lecture-notes/)、[Olah-style-posts](https://github.com/1998x-stack/Olah-style-posts)。文章和图解均重新组织，不复制其示例的图文。
