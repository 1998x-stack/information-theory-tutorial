# AGENTS.md — Information Theory Tutorial

## 教材目标

28 篇网页均须独立成篇：定义先行、符号清楚、推导准确、图例可理解、算例可复现。不要写“讲义介绍了……”或只给目录式简介。按真实科研与教材标准审校，优先阅读对应原版章节和经典来源，不为图解效果牺牲数学事实。

## 目录责任边界

- 维护源：`src/home/index.html`、`src/chapters/{NN}.html`、`src/assets/`、`src/figures/`、`src/data/courses.json`。
- 构建产物：`docs/` 由 `scripts/build.py` 复制生成，不能只修改 `docs/`；根目录 `index.html` 与 28 个兼容重定向同为产物。
- 06–28 章仍用旧版布局，并引用 `docs/chapters/theme.css`；未重构前必须保留对应 `src/assets/legacy.css`。

## 逐章工作流

1. 先审旧正文和章节图谱，给读者一个真实问题，再写从直觉到可检验结论的因果学习路线。
2. 核查教材/原论文、公开大学课程两类依据；关键结论按章节写入 `research/evidence.json`。
3. 写符号表与前提：离散/连续、概率支持集、自然对数还是 log₂、条件独立等。缺失时不得声称定理普遍成立。
4. 公式优先原生 MathML（`mfrac`/ `munderover`/ `msub`），每条关键式要有 aria-label，长式放在可聚焦、可横向滚动的容器。SVG 内不得嵌套 MathML。
5. 使用独立原创 SVG：`xmlns/viewBox/title/desc`，明确箭头方向、变量含义、分布归一化、单位与适用条件，图注不能仅复述标题。
6. 提供具有固定种子的、可以断言的最小计算例；交互为渐进增强，默认结果不依赖 JavaScript，原生 range/button 可键盘操作并更新 output。
7. 运行 `python3 scripts/build.py && python3 scripts/build.py --check && python3 scripts/validate.py && python3 -m unittest discover -s tests`。
8. 额外浏览器验收 1440、390、360 像素、键盘聚焦、SVG、数学式布局、无页面横溢、打印、控制器输出和全部本地链接。若未执行应写明“未验证”，不能伪称通过。

## 容易出错的技术约束

- (I(X;Y)) 非 Pearson 相关性，相关为 0 不等于独立。
- (D(P\|\|Q)) 不对称、不是距离；当 p(x)>0 且 q(x)=0 时为无穷大。
- 数据处理不等式需要马尔可夫链 X→Y→Z 条件独立假设。
- 离散熵中 0 log 0 按极限约定为 0；概率总和应为 1。
- 不可把单次 toy 计算说成一般性数学证明。

## 外部规范与来源

- https://github.com/1998x-stack/Olah-style-posts/tree/main/skills/olah-style-paper-posts
- https://doi.org/10.1002/j.1538-7305.1948.tb01338.x
- https://onlinelibrary.wiley.com/doi/10.1002/0471200611.ch2
- https://ocw.mit.edu/courses/6-441-information-theory-spring-2010/pages/lecture-notes/
