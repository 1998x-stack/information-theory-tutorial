# AGENTS.md — Information Theory Tutorial

## 教材目标

28 篇网页均须独立成篇：定义先行、符号清楚、推导准确、图例可理解、算例可复现。不要写“讲义介绍了……”或只给目录式简介。按真实科研与教材标准审校，优先阅读对应原版章节和经典来源，不为图解效果牺牲数学事实。

## 目录责任边界

- 维护源：`src/home/index.html`、`src/chapters/{NN}.html`、`src/assets/`、`src/figures/`、`src/data/courses.json`。
- 构建产物：`docs/` 由 `scripts/build.py` 复制生成，不能只修改 `docs/`；根目录 `index.html` 与 28 个兼容重定向同为产物。
- 全部 01–28 章已改用统一 `site.css` 与 `site.js`；`src/assets/legacy.css` / `docs/chapters/theme.css` 仅保留作历史兼容，不能用于新增内容。

## 逐章工作流

1. 先审旧正文和章节图谱，给读者一个真实问题，再写从直觉到可检验结论的因果学习路线。
2. 核查教材/原论文、公开大学课程两类依据；关键结论按章节写入 `research/evidence.json`。
3. 写符号表与前提：离散/连续、概率支持集、自然对数还是 log₂、条件独立等。缺失时不得声称定理普遍成立。
4. 公式优先 MathML Core（`mfrac`/ `munderover`/ `msub`），每条关键式要有 aria-label，长式放在可聚焦、可横向滚动的容器。不要使用已从 MathML Core 移除的 `mfenced`；矩阵括号用 `mrow` + `mo` 明确构造。SVG 内不得嵌套 MathML。
5. 使用独立原创 SVG：`xmlns/viewBox/title/desc`，明确箭头方向、变量含义、分布归一化、单位与适用条件，图注不能仅复述标题。
6. 提供具有固定种子的、可以断言的最小计算例；交互为渐进增强，默认结果不依赖 JavaScript，原生 range/button 可键盘操作并更新 output。
7. 运行 `python3 scripts/build.py && python3 scripts/build.py --check && python3 scripts/validate.py && python3 -m unittest discover -s tests`。
8. 运行 `python3 scripts/browser_smoke.py` 完成 Chromium 验收 1440、768、390、360 像素、键盘聚焦、MathML namespace/几何、SVG 实际加载、无外部运行时依赖、无页面横溢、打印和所有交互输出。`scripts/validate.py` 还必须验证 MathML XML 结构、公式限位节点、重复 ID、全部本地文件与片段链接、导航和实验脚本映射。若未执行应写明“未验证”，不能伪称通过。

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

- 多用户容量域必须注明信道模型、输入独立性、实/复维度和每次使用单位。两用户实高斯 MAC 三条约束分别是两个单用户上限与总和速率上限；MAC SIC 角点由解码顺序决定。
- 退化广播信道的叠加编码结论不得推广到一般非退化 BC。Relay 的 cut-set 是上界、decode-forward 是可达下界；一般中继容量未必已知。干扰信道要说明干扰系数和解码策略；网络编码示例要写清侧信息。
- Fisher 信息与 Cramér–Rao 界需要可微性、支持集等正则条件；参数依赖支撑集的模型（如 U(0,θ)）不能机械套用标准 CRLB。n 个 i.i.d. 样本的 Fisher 信息相加。
- MDL 是描述长度原则族，不应等同于单一 MAP 公式。AIC 近似预测 KL 风险，BIC 是边际似然的 Laplace 近似；记录自然对数、参数数目、样本独立性与模型正则条件。
- 最大熵必须列明约束；“最随机”只在给定约束类内有意义。不要把最大熵解直接称为真实生成分布。
- Softmax + CE 对 logits 的梯度为 q−y，目标 y 应是归一化概率。Brier / squared error 是适当评分规则，不能声称 MSE 没有概率解释或 CE 在所有任务上必胜。Label smoothing、distillation 与 VAE KL 是不同目标。
- VAE ELBO 的重构项取决于观测似然；Bernoulli 对应 BCE，固定方差 Gaussian 对应带尺度的平方误差。KL 项比较近似后验与先验。
- IB 假设 T−X−Y；经典目标与 VIB KL 权重约定须明确。连续 X 的确定性连续表示可能导致 I(X;T) 发散；信息平面压缩轨迹不是普遍深度学习定律。
- 离散插件熵在固定支持集有限样本下通常向下偏；Miller–Madow 是一阶近似修正。经验 MI 在独立性原假设下常有正偏。KSG 的单位默认 nats，转 bits 需除 ln 2；KSG、KDE、MINE 与 InfoNCE 的假设不同。
- InfoNCE 是受负样本数约束的互信息下界，通常至多 log(K) nats；MINE 的 DV 目标是总体分布下界，有限样本训练值不保证是无偏估计。所有 MI 实验必须报告估计器、参数、单位、样本量、随机种子和不确定性。

- 语义通信必须首先定义 X、上下文 K、任务/语义变量 S=g(X,K)、失真函数 d 与假设；同义词嵌入的 cosine similarity 不是概率，不能对其随意取 −log₂ 并称“语义熵”。S 的条件熵 H(S|K) 在确定性映射时不超过 H(X|K)，并不意味着物理信道容量因此提高。
- 任务率失真 R(D) 的二元闭式 1−h₂(D) 只适用于 i.i.d. 等概 Bernoulli、Hamming 失真与渐近块长。语义编码必须另计模型、算力、同步、元数据和物理传输开销。ITU-R 的 AIAC 使用场景不是统一语义通信协议认证。
- 量子密度矩阵需要 Hermitian、半正定、迹一；von Neumann 熵由特征谱计算。Bell 态全局纯、局部最大混合，量子互信息是 2 bit 且永不为负。Holevo 约束须注明无预共享纠缠的资源口径，超密编码并不违规。
- 传递熵 T(X→Y)=I(Y_{t+1};X_t|Y_t) 是指定历史深度的条件预测增益，单凭非零 TE 不能声称因果。若有共同驱动、反馈、非平稳性与估计偏差，需要专门的因果可识别性假设及控制。
- PID 非唯一，须指定分解公理/冗余定义；独立公平 X1/X2 的 XOR 输出是纯协同的可解析示例。Landauer kBT ln2 下界针对等概率未知经典比特的准静态不可逆擦除，不能套到所有计算操作。
- 综合项目需要双向往返测试和端到端检验；Huffman 元数据、变长码错误传播、算术编码有限精度协议、LZW 码宽封装、Hamming 双错误纠正、BSC 种子与码率必须显式描述。不得把固定样本包的总发送比特数说成不包含码本/帧头的真实压缩率。
- 发布前必须验证全部 28 篇：原生 MathML、SVG title/desc、每篇交互、移动端 1440/390/360、全文打印与 CI 产物。全站 88 张独立 SVG 的数量变更需同步元数据与验收。
