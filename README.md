# 信息论 · 从概率到通信极限

[课程首页（GitHub Pages）](https://1998x-stack.github.io/information-theory-tutorial/) · [源码仓库](https://github.com/1998x-stack/information-theory-tutorial)

28 章中文信息论教程，从概率、熵、互信息走到压缩、可靠通信、统计学习和信息瓶颈。**全 28 章已完成六批深度精修（88 张独立 SVG、30 个交互实验）；第 28 章有真正可运行的端到端 Huffman–Hamming–BSC 项目。**

## 本地阅读与构建

```bash
python3 scripts/build.py
python3 scripts/build.py --check
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
# 可选本地浏览器验收：pip install playwright && python -m playwright install chromium
# python3 scripts/browser_smoke.py
python3 -m http.server 8000     # http://localhost:8000/docs/
```

用 `python3 -m examples.capstone` 运行项目，或用 `python3 -m unittest tests.test_capstone -v` 运行专门的综合项目测试。无需 Node.js 或 CDN，静态 HTML 在现代浏览器中无需网络即可阅读。站外参考链接需要联网。

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
  chapters/theme.css      # 历史原版样式存档（新版页面均用 site.css）
  assets/css, assets/js, assets/figures
scripts/build.py          # 构建 & --check 一致性校验
scripts/validate.py       # 链接、SVG 和基本 HTML 验收
examples/foundations.py   # 离散信息量计算样例
examples/coding.py        # Huffman、Kraft、精确算术编码及译码
examples/channel_coding.py # LZ77/LZ78、容量、块错误、Hamming(7,4)
examples/advanced_information.py # CRC、Viterbi、OTP、率失真、微分熵与高斯信道
examples/information_learning.py # 多用户容量、统计推断、CE/IB 与互信息估计
examples/capstone.py      # 熵/KL、Huffman、精确算术编码、LZW、Hamming + BSC 闭环
tests/                    # 全课程数值、往返、单错纠正、随机噪声、统计学习断言
research/evidence.json    # 关键论断的来源
scripts/browser_smoke.py  # Playwright 浏览器视觉与交互烟测
AGENTS.md                 # 章节维护规范
```

根目录的 `01.html`…`28.html` 与 `index.html` 保留兼容跳转到 `docs/`。既有 Pages 使用仓库根目录时无需改源设置；若配置为 `/docs` 则直接使用 `docs/index.html`。实际 Pages 是否发布成功须在部署后验证。

## 综合项目的计量边界

第 28 章仅对源编码正文计数（例如 AAAABBCD 的 Huffman 正文为 14 bit），不把预共享码本、原始正文长度、帧头和模型更新成本算进裸比特数。Hamming(7,4) 只能纠正每个 7-bit 码字的 1 位错误，双错可能产生误纠正。算术编码的 `Fraction` 演示不等于生产环境的流式有限精度文件协议，LZW 返回的整数码也未序列化为真实字节数。比较吞吐量必须统一物理信道使用次数和完整开销。

## 编辑规范

按 [AGENTS.md](AGENTS.md) 中的逐篇流程维护文章。所有数学式明确基底、支持集和零概率约定；优先使用离线原生 MathML；SVG 要有独立标题、描述和图注，移动端阅读、键盘操作和屏幕阅读器均需验收。

资料与方法参考：Shannon (1948)、Cover & Thomas (2006)、[MIT 6.441](https://ocw.mit.edu/courses/6-441-information-theory-spring-2010/pages/lecture-notes/)、[Olah-style-posts](https://github.com/1998x-stack/Olah-style-posts)。文章和图解均重新组织，不复制其示例的图文。
