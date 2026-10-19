# ScrapeBench：WWW 2027 模拟审稿意见与修改清单

> 评审对象：`11(1).pdf`，10 页初稿。  
> 当前论文题目：*ScrapeBench: Benchmarking and Defending Face Anti-Customization as an Acquisition Contract on the Agentic Web*  
> 评审性质：模拟三位 WWW Research Track 审稿人的学术意见，**不代表 WWW 官方评审结果**。  
> 评分方式：本报告采用自定义 1–5 分尺度（1 = Strong Reject；2 = Reject；3 = Borderline；4 = Weak Accept；5 = Strong Accept），不声称这是 WWW 官方统一打分制。

## 一、执行摘要：总体评价

**模拟结论：Borderline / Reject / Reject，综合倾向 Reject（当前版本）。**

该工作提出了一个具有 WWW 相关性的研究问题：**人脸反定制保护在原始上传文件上的有效性，能否在真实 Web 图像获取操作后继续保持？** 论文将这一偏差称为 *Web Acquisition Gap*，并提出 ScrapeBench 独立获取条件的评测协议、ARCP-Web 对抗扰动优化，以及 `face-consent.txt` 的授权声明方向。

当前最主要的审稿风险包括：

1. **实验规模不足**：正式结果只有 4 个身份；40 身份是已审计的扩展池，而非完成的完整防御实验。
2. **ARCP-Web 缺少关键消融**：尚不能证明弱层调度、纹理分配和多尺度扰动各自带来的效果。
3. **防御与定制基线不够充分**：特别是针对 InstantID / IP-Adapter-FaceID 的 IDProtector 缺席；DreamBooth 微调实验尚未成为完成的主结果。
4. **Web 场景的端到端真实性仍有限**：主要依赖模拟的压缩、缩放、截图裁剪与生成式变换，而非完整的平台上传—抓取链路。
5. **协议主张偏强**：`face-consent.txt` 尚无充分的来源绑定、传播、授权校验、撤销与实际 Agent 执行证据。
6. **图表、正文和预算存在不一致**：具体见第六部分。

研究方向值得继续推进；优先修复核心证据链，胜过只优化文字和配图。

---

## 二、论文内容概述

### 2.1 研究问题

以往反定制研究多直接评估加入扰动后的原始图片，假设攻击者下载到的就是同一份文件。但在 Web 上，图片可能经过 CDN 重编码、缩略图渲染、人脸裁剪、增强与重新生成，再被身份定制模型使用。这样的变化可能改变保护效果。

### 2.2 三项工作内容

**ScrapeBench（评测）**：从同一 T0 图像分别施加七个独立条件（非 T0→T6 累积流水线），使用匹配的 Clean / Protected 分支、独立 held-out 身份参考、相同 prompts / seeds 和 Clean Validity Gate，测量防御的实际保护差距。

**ARCP-Web（算法）**：通过粗细两级扰动网格、纹理感知幅度、扩散去噪与人脸身份的联合目标，以及当前最弱 acquisition layer 的自适应调度，使受保护图片尽量在 Web 处理后仍干扰身份定制。

**`face-consent.txt`（授权声明方案）**：设想通过 `/.well-known/face-consent.txt` 声明某些图像及主体对应的使用许可、过期、撤销与可选签名，以支持合规平台和 Agent 在像素扰动失效时仍查询授权状态。**当前应视为提议或设计方向，不能宣称已自动随图片传播并实现强制执行。**

### 2.3 七个独立获取条件（PDF 第 3 页 Table 1）

| 条件 | 实验操作 | 场景含义 |
|---|---|---|
| T0 | Original protected upload | 原始发布文件 |
| T1 | JPEG Q70、4:2:0、512 px | CDN 转码 |
| T2 | 360-px CSS raster、DPR 1 | 页面/缩略图渲染 |
| T3 | Detector crop、margin 0.35、WebP 80 | 截图/人脸裁剪 |
| T4 | Real-ESRGAN ×2 | 图像增强 |
| T5 | SD1.5 img2img、strength 0.30 | 生成式重新上传 |
| T6 | Prompt-free SD1.5 reconstruction、strength 0.50 | 净化代理 |

### 2.4 当前已有实验

- **身份**：完成 4 身份 pilot；每身份 4 张 gallery、2 张 held-out reference；另有经过预审的 40 身份扩展池。
- **防御**：Clean、GAP-Diff、MetaCloak、GoodAC、ARCP-Web。
- **身份定制模型**：InstantID 和 IP-Adapter-FaceID；DreamBooth 被列为第二阶段、尚未在当前主结果中完整呈现。
- **论文主要观察**：在 11 个被判定可排名的 reader–layer 条件里，ARCP-Web 在 9 个条件取得最大 **点估计** 保护差距，但并非全部差异已经得到与次优方法比较的统计支持。
- **上传质量**：PDF 第 7 页 Table 5 报告 ARCP-Web PSNR 37.80 dB、实际 `L∞ = 8/255`；GoodAC 为 33.45 dB、8/255；GAP-Diff 为 31.68 dB、9/255；MetaCloak 为 29.76 dB、11/255。
- **限制**：4 个身份不足以支持广泛人群的效果或泛化结论；T4/T6 等某些条件存在 clean attack 本身失效，不应进入防御排名。

---

## 三、Reviewer #1：Web 系统 / Benchmark 专家

**模拟评分：3/5（Borderline）**  
**模拟信心：4/5**

### Strengths

- 把 Web 获取过程当作影响身份隐私防御的独立变量，选题与 WWW 相关。
- Clean/Protected 匹配分支、独立 T0–T6 以及有效性门槛让评测更可解释。
- 区分压缩、网页渲染、抓取裁剪和模型介导的再生成，具备构建评测工具的潜力。

### Major Weaknesses

1. **代表性不足**：仅 4 个身份和预设的单一参数集，尚不能证明 benchmark 结论的稳定性。
2. **Web 真实性不足**：需要展示实际平台上传、服务端转码、浏览器渲染、爬虫获取再用于身份定制的闭环。
3. **操作选择依据不充分**：JPEG Q70、CSS 360 px、固定裁剪边界等参数需要实测分布或已有明确来源支撑。
4. **单步与真实流水线之间存在差距**：单步归因有意义，但不能自动代表连续、多次重编码的 Web 获取过程。

### 审稿人关键问题

> How does ScrapeBench move beyond a collection of standard image transformations to become a genuinely Web-specific evaluation framework?

### 建议修改

- 跑完整 40 身份，报告各身份和各来源分布。
- 增加至少一个真实端到端 Web serving / scraping 对照。
- 对参数选取做服务测量与敏感性分析。
- 保持单步实验为主，并以少量多步链路作为外部有效性验证。

---

## 四、Reviewer #2：对抗防御 / 生成模型专家

**模拟评分：2/5（Reject）**  
**模拟信心：5/5**

### Strengths

- ARCP-Web 将 coarse/detail 扰动、texture-aware allocation、多个获取代理和最弱层调度结合起来，研究思路合理。
- 有明确像素幅度预算，报告身份相似度、检测失败和 PSNR。
- 承认部分 acquisition layer 上的效果不足，而非完全宣称万能防御。

### Major Weaknesses

1. **样本过小**：bootstrap 置信区间不能替代更多独立身份；不能用 4 个身份证明稳定 SOTA 排名。
2. **缺少消融**：无法归因到弱层调度、粗细网格、纹理感知、identity loss、diffusion loss。
3. **缺少 IDProtector 等针对性强基线**：现有主要攻击是 encoder-based zero-shot customization，而该类防御有专门方法。
4. **评价器重叠**：优化使用 ArcFace/FaceNet 相关身份目标，最终评估又主要依赖 ArcFace；应补未见的独立识别器。
5. **预算不完全同一**：8/255、9/255、11/255 不可直接称为严格 common-budget 对比。
6. **零样本与训练式主张不匹配**：DreamBooth 第二阶段未完成，不能据此宣称同时防住所有 fine-tuning 与 zero-shot attacks。

### 审稿人关键问题

> Is the improvement caused by the weakest-layer scheduler, or mostly by the reader-targeted identity loss and differing baseline implementations?

### 最重要的消融矩阵

| 消融 | 需要回答的问题 |
|---|---|
| Full ARCP-Web vs Uniform EOT | 最弱层自适应调度是否有用？ |
| w/o texture mask | 纹理分配是否改善视觉质量/保护效果？ |
| w/o coarse grid | 粗尺度是否提高压缩鲁棒性？ |
| w/o detail grid | 细尺度是否提高 pristine 或 reader 层效果？ |
| w/o identity objective | 编码器身份攻击目标贡献多少？ |
| w/o denoising objective | 训练投毒目标贡献多少？ |

### 建议修改

- 完成 40 身份并以 identity 为统计独立单元。
- 优先加入 IDProtector，若资源允许加入 PhotoMaker、PuLID / DiT 管线，保持方法针对性匹配。
- 在同一实际 8/255 预算下报告能合法适配的方法；另列 official-default 对比，不能混为一组。
- 直接对 **ARCP 与最强 baseline 的 gap 差值** 给出配对置信区间，不能由各自 vs 0 显著推出彼此显著。
- 将绝对保护差距及其变化作为主要指标；当 `Δ0` 为零或负数、或接近零时不将 RR 作为可靠排名依据。

---

## 五、Reviewer #3：Web 隐私 / Consent 协议专家

**模拟评分：2/5（Reject）**  
**模拟信心：4/5**

### Strengths

- 明确指出“照片公开可见”并不等于“本人允许被用于身份定制”。
- 承认强重建下像素扰动可能无法保持，从而讨论基于 Web 系统的授权路径。
- Web 来源记录和可审计授权是 WWW 有意义的议题。

### Major Weaknesses

1. **授权主体不明确**：网站上传者、摄影者、照片主体不一定相同；谁可以代表人脸主体授权？
2. **传播机制尚不充分**：跨域转载、截图、重编码、裁剪之后，如何找到原始 manifest？
3. **缺少完整原型和评估**：需要解析/验证/查询/撤销/签名与真实 Agent 执行流程。
4. **没有强制安全保证**：恶意 Agent 可忽略 `face-consent.txt`，不能把它描述成能自动阻止未经许可身份定制。
5. **既有机制对比不足**：需系统比较 C2PA、`robots.txt`、来源信息和 AI 数据使用许可相关方案。

### 审稿人关键问题

> What concrete security or consent guarantees are provided beyond a voluntary machine-readable usage preference?

### 建议修改

**方案 A（投稿时间紧时推荐）**：将 `face-consent.txt` 降级为 Discussion 中的设计方向；只声明它有助于合规查询与审计，不宣称已经随图像传播或强制执行。

**方案 B（作为独立系统贡献）**：实现上传者/图片主体校验、manifest 定位、重编码后的内容绑定、撤销及冲突规则，并实测浏览器、CDN、爬虫和 Agent 的执行过程。

---

## 六、需要立即修正的具体问题（基于当前 PDF）

### 6.1 Figure 1 与 Table 1 的 T0–T6 含义不一致

第 2 页 Figure 1 的底部标注包含 consent layer、recompression、watermark、prompt variants 等，而第 3 页 Table 1 明确规定 T0–T6 为 original/JPEG/feed raster/crop/Real-ESRGAN/img2img/purification。

**修改：** 统一所有图、表、文本、代码中的 intervention registry；Figure 1 应突出 Web acquisition 缺口，而不要塞入冲突的 T 定义。

### 6.2 Figure 2 的无效条件概括过宽

第 4 页 Figure 2 caption 将 T4–T6 近似整体描述为 gate-invalid；但主表显示 InstantID T5 有效，IP-Adapter-FaceID T4/T5 也可排名。

**修改：** 按每个 reader 逐项说明有效性，而非一概否定 T4–T6。

### 6.3 Figure 4 的 common-budget 表述与 Table 5 不一致

Table 5：GAP-Diff = 9/255，MetaCloak = 11/255，GoodAC 和 ARCP-Web = 8/255。

**修改：** 图注不能声称四种方法全都完成 common 8/255 实际预算的对比。将官方默认预算与严格同预算分开。

### 6.4 ARCP-Web 的训练数据尺度与代理实现

PDF 明确记录 JPEG 代理曾需修正 `[-1,1]` → `[0,1]` 转换，否则会裁剪输入。

**修改：** 报告修复后所有训练结果是否重新生成、代理和真实测试变换的差异、扰动实际像素预算和生成所需计算量。

### 6.5 没有充分证明 ARCP 优于次优方法

“在 9/11 个有效列里点估计第一”不等于“在 9/11 个条件上显著优于所有 baselines”。

**修改：** 对差值 `Δ_ARCP − Δ_baseline` 做同身份配对 CI 或相应检验，并明确处理多重比较。

### 6.6 Clean Validity Gate 与实验样本解释

例如 InstantID clean T0 的检测失败率为 37.5%，应清楚解释第 5.2 节预检（smoke test）75% 有效生成门槛与后续正式 cell 的 50% rankability gate 的关系。

**修改：** 用一张流程表明确不同 gate 的样本数量、前置条件与失败后的处理。

### 6.7 过强的表述

- “consent travels with the image” 当前没有端到端追踪和强制执行证据。
- “dominates all baselines under a common 8/255 budget” 受实际扰动预算影响。
- “robust against training-based customization” 缺少完成的 DreamBooth 主结果。

**修改：** 采用被验证的、按读者与 acquisition layer 限定的描述，避免总体化结论。

---

## 七、按优先级安排补实验

| 优先级 | 任务 | 所要化解的审稿质疑 |
|---|---|---|
| **P0** | 完成并审计 40 身份的主要结果 | 小样本与外部有效性 |
| **P0** | 补 IDProtector × InstantID / IP-Adapter-FaceID | 零样本防御基线缺席 |
| **P0** | Full ARCP-Web vs Uniform EOT + 核心消融 | 最弱层调度的必要性 |
| **P0** | 严格同预算对比 + 官方默认设置单独报告 | baseline 公平性 |
| **P0** | 修正文中各图表/指标/有效性门槛不一致 | 可重复性与可信度 |
| **P1** | 至少一个真实平台或自控 Web 服务的上传—抓取—生成闭环 | Web 特有性 |
| **P1** | 独立身份评估器、更多随机种子、配对差值显著性 | 评价偏置与统计功效 |
| **P1** | PhotoMaker / PuLID 等另一路身份定制 | attack model 覆盖 |
| **P1** | T0、T1、T3 等代表性条件的连续操作验证 | 单步与真实链路之间差距 |
| **P2** | 实现并评估 consent 原型 | 协议系统贡献 |
| **P2** | 完整 DreamBooth 训练式定制 | 双类攻击主张 |

> **资源有限时的推荐取舍：** 先做 40 身份 + IDProtector + 弱层调度消融 + 同预算修正。额外模型数量不如核心对照可靠重要。

---

## 八、论文标题建议

### 首选（Benchmark 主导）

**ScrapeBench: Evaluating Face Anti-Customization under Web Image Acquisition**

优点：直接点出研究对象，不使用读者难以理解的 *Acquisition Contract*，也不要求算法、协议必须都已达到完整系统贡献的强度。

### 如果 ARCP-Web 完成强消融并成为主要贡献

**ScrapeBench: Measuring and Improving Face Protection across Web Acquisition Pipelines**

### 强调动机与 Web 场景

**Beyond Pristine Images: Benchmarking Face Anti-Customization on the Web**

### 强调评测与防御双线

**ScrapeBench: Acquisition-Aware Evaluation and Defense for Facial Identity Protection**

**不建议在题目中同时堆叠** `Benchmarking and Defending`、`Acquisition Contract` 和 `Agentic Web`，否则技术焦点变得不清晰，也容易放大未验证的协议/Agent 主张。

---

## 九、修改后建议的章节结构

1. **Introduction** — Web Acquisition Gap、清晰研究问题及三项限定贡献。
2. **Threat Model & Web Acquisition** — 真实操作来源、威胁边界、参数测量。
3. **ScrapeBench** — 独立干预、匹配对照、有效性门槛和统计指标。
4. **ARCP-Web** — 粗细扰动、纹理幅度、联合目标和 weakest-layer 调度。
5. **Experiments** — 40 身份主实验、多防御/多 reader 对比、真实 Web 获取验证。
6. **Analysis** — 完整消融、视觉质量、异常值和失败案例。
7. **Discussion** — Consent 设计、部署要求、威胁边界与伦理。
8. **Conclusion** — 严格按完成实验支持的范围写结论。

建议将论文主要研究问题组织为：

- **RQ1：** Web 获取操作如何改变同身份的保护差距？
- **RQ2：** 这种变化是否依赖防御设计与个性化攻击机制？
- **RQ3：** 优化当前最弱的获取条件是否优于平均多变换优化？
- **RQ4：** 哪些条件下仅靠像素保护不足，需要合规的 Web 授权与审计机制？

---

## 十、提交前自检表

- [ ] 40 身份实验真正完成并和摘要/结论一致
- [ ] 关键 Zero-shot Baseline（至少 IDProtector）加入
- [ ] 弱层优化 vs Uniform EOT 完成
- [ ] 纹理/粗细尺度/各损失组件消融完成
- [ ] 所有比较的实际扰动预算说明清楚
- [ ] 引入至少一个未见身份评估器
- [ ] Gap、Gap change、置信区间与多重比较处理清楚
- [ ] RR 分母接近零或为负时有明确处理规则
- [ ] 图 1、图 2、图 4 与 Table 1、Table 5 完全一致
- [ ] 真实 Web 参数由实测或可重现证据支撑
- [ ] `face-consent.txt` 的贡献定位和实现证据匹配
- [ ] PDF 的匿名、版式、页数与引用信息符合目标 Track 当年 CFP

---

## 十一、最终评审结论

**目前倾向 Reject 的根本原因是证据成熟度，而不是研究动机差。** ScrapeBench 的独立 Web acquisition + matched clean validity gate 有研究价值；ARCP-Web 最可能产生算法创新的是 weakest-layer adaptive optimization。但现在仅有四身份 feasibility pilot，缺少强针对性防御、充分消融和真实 Web acquisition 闭环。将这些补齐，并收紧协议和泛化结论后，稿件才有更强的 WWW 竞争力。

**推荐立即执行的顺序：** 核心实验真实性/规模 → 强 baseline → 调度消融 → 统计对比 → 修正全文和图表 → 标题/语言润色。

---

*说明：本文件整理的是本轮对你已上传 PDF 的模拟审稿意见，外部文献真实性核验不在此报告覆盖范围之内；具体接收标准和投稿日程请以 WWW 2027 官方 CFP 为准。*
