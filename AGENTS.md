# AGENTS.md — Information Theory Tutorial

## 教材目标

28 篇网页均须独立成篇：定义先行、符号清楚、推导准确、图例可理解、算例可复现。不要写“讲义介绍了……”或只给目录式简介。按真实科研与教材标准审校，优先阅读对应原版章节和经典来源，不为图解效果牺牲数学事实。

## 目录责任边界

- 维护源：`src/home/index.html`、`src/chapters/{NN}.html`、`src/assets/`、`src/figures/`、`src/data/courses.json`。
- 构建产物：`docs/` 由 `scripts/build.py` 复制生成，不能只修改 `docs/`；根目录 `index.html` 与 28 个兼容重定向同为产物。
- 21–28 章仍用旧版布局，并引用 `docs/chapters/theme.css`；未重构前必须保留对应 `src/assets/legacy.css`。

## 逐章工作流

1. 先审旧正文和章节图谱，给读者一个真实问题，再写从直觉到可检验结论的因果学习路线。
2. 核查教材/原论文、公开大学课程两类依据；关键结论按章节写入 `research/evidence.json`。
3. 写符号表与前提：离散/连续、概率支持集、自然对数还是 log₂、条件独立等。缺失时不得声称定理普遍成立。
4. 公式优先原生 MathML（`mfrac`/ `munderover`/ `msub`），每条关键式要有 aria-label，长式放在可聚焦、可横向滚动的容器。SVG 内不得嵌套 MathML。
5. 使用独立原创 SVG：`xmlns/viewBox/title/desc`，明确箭头方向、变量含义、分布归一化、单位与适用条件，图注不能仅复述标题。
6. 提供具有固定种子的、可以断言的最小计算例；交互为渐进增强，默认结果不依赖 JavaScript，原生 range/button 可键盘操作并更新 output。
7. 运行 `python3 scripts/build.py && python3 scripts/build.py --check && python3 scripts/validate.py && python3 -m unittest discover -s tests`。
8. 运行 `python3 scripts/browser_smoke.py` 完成浏览器验收 1440、390、360 像素、键盘聚焦、SVG、数学式布局、无页面横溢、打印、控制器输出和全部本地链接。若未执行应写明“未验证”，不能伪称通过。

## 容易出错的技术约束

- (I(X;Y)) 非 Pearson 相关性，相关为 0 不等于独立。
- (D(P\|\|Q)) 不对称、不是距离；当 p(x)>0 且 q(x)=0 时为无穷大。
- 数据处理不等式需要马尔可夫链 X→Y→Z 条件独立假设。
- 离散熵中 0 log 0 按极限约定为 0；概率总和应为 1。
- AEP 的 i.i.d. 版本须注明独立同分布；有限 n 的典型集概率未必接近 1，不能混淆近乎无损与完全无损编码。
- Huffman 的最优性仅指给定符号分布下最短平均前缀码；编码树的父子关系必须与实际码字相符。
- 算术编码须用旧边界同时更新新上下界；教学版有理数区间并不等于可交付的有限精度位流协议。
- 不可把单次 toy 计算说成一般性数学证明。
- 区分 LZ77 回距与 LZ78 词典索引；DEFLATE 的 LZ77+Huffman 二阶段和 gzip 封装不能混淆。
- 信道条件核 W(y|x) 每行必须归一化；互信息 I(X;Y) 不等于对输入优化后的容量 C；对非对称信道必须测试非均匀先验。
- 信道编码定理的可靠性是随块长增长、R<C 的渐近存在性结论，不是有限长度任意码的承诺。
- Hamming(7,4) 的位置与 H 矩阵列序必须一致，syndrome=5 对应第 5 位翻转；不可把多错当成可纠正单错。

## 外部规范与来源

- https://github.com/1998x-stack/Olah-style-posts/tree/main/skills/olah-style-paper-posts
- https://doi.org/10.1002/j.1538-7305.1948.tb01338.x
- https://onlinelibrary.wiley.com/doi/10.1002/0471200611.ch2
- https://ocw.mit.edu/courses/6-441-information-theory-spring-2010/pages/lecture-notes/

- CRC 的漏检条件是 G(x) 整除错误多项式 E(x)；次数 r、常数项为 1 的生成多项式可检出所有长度不超过 r 的突发错误。随机漏检概率近似必须注明错误模型。标准 CRC 还要记录 init/refin/refout/xorout；CRC 不是 MAC。
- 卷积码必须明确寄存器状态位序、生成多项式、输入/输出顺序、初态和终态。Viterbi 的分支度量由信道模型决定；硬判决汉明距离与软判决似然不能混称。
- 完善保密要求 I(M;C)=0。H(K)≥H(M) 是正确解密系统的必要条件，不是充分条件；OTP 要求密钥均匀、独立、等长、保密且只使用一次。
- 率失真函数依赖源分布与失真函数，约束是期望块平均失真；高斯平方误差公式不能推广到任意源/感知度量。向量高斯源的反向注水应区分单标量公式。
- 微分熵会随坐标尺度变化；h(aX+b)=h(X)+log₂|a|。高斯最大熵需注明协方差约束。实值 AWGN 每次使用容量含 1/2；带宽容量需单独说明自由度归一化。并联高斯信道注水与源编码反向注水方向相反。
