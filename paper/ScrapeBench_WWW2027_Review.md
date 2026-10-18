# WWW 2027 模拟审稿报告：ScrapeBench

> **论文题目**：*ScrapeBench: Anti-Customization Face Protections Collapse Under Real-Web Image Acquisition*
> **评审视角**：The Web Conference 2027（WWW 2027）Research Track；重点关注 Web Security & Privacy、Responsible Web 和 Benchmark Evaluation。
> **评审性质**：模拟同行评审，不代表 WWW 2027 官方审稿结果。
> **评审依据**：作者提供的 12 页论文 PDF（正文及附录）。涉及学术定位、其他研究和会务信息的意见为评审建议，应以相应论文及 WWW 2027 官方 CFP 核实。

## 一、总体评价与接收判断

- **模拟总体评分：4/10**（非官方量表）
- **模拟审稿结论：Weak Reject（偏向拒稿）**
- **审稿信心：4/5**

**核心判断：这篇论文具备 WWW 主会所需要的问题意识和现实意义，但当前版本的实验严谨性不足以支撑标题和摘要中较强的结论。**

论文最大的价值在于指出：现有面部反个性化保护方法通常在理想图像文件上评估，而实际 Web 环境包含平台压缩、浏览器渲染、截图、裁剪和图像再生成等过程。作者进一步提出 ScrapeBench、Retention Ratio（RR）以及与身份匹配的评估协议。这是一条值得投稿 WWW 的研究方向。

真正的问题在于：**论文想证明“现有保护在真实 Web 获取条件下失效”，但目前的数据更有力地证明的是“保护效果对评估协议、采集变换和生成模型高度敏感”。** 两者并不等价。

更严重的是，附录 A.1 承认原始主实验中 clean 和 protected 图像进入模型前采用了不同的几何预处理，修复后的完整主实验没有重新报告。对于一篇把 *fair evaluation* 作为核心贡献的 benchmark 论文，这会直接影响审稿人对结果可信度的判断。

### 与 WWW 研究论文的匹配程度

| 维度 | 评价 |
| --- | --- |
| Web 相关性 | 强 |
| 问题重要性 | 强 |
| 创新性 | 中上 |
| 技术正确性 | 存在重大疑问 |
| 实验充分性 | 偏弱 |
| 可复现性 | 有良好设计，但需实际验证 |
| 写作与组织 | 较好，部分结论过度强化 |
| 当前接收竞争力 | 偏弱 |

从投稿定位看，更倾向于 Research Track 中的评估／资源类方向，其次是 Security and Privacy。如果进一步强化用户同意机制与平台治理的实证部分，也可以考虑 Responsible Web 相关方向；**具体 track 名称、要求和资格请以当年官方 CFP 为准**。

---

## 二、值得保留的三个贡献（Strengths）

### Strength 1：Web Acquisition Gap 是有价值的问题定义

论文将防御者上传的图像与攻击者最终获得的图像区分开来，并将中间过程分解为 T0–T6 七个层级（论文第 3–4 页）。

尤其值得强调的是，作者不仅模拟 JPEG、WebP、canvas rendering，还尝试通过 GitHub Avatar、Gravatar、WordPress Photon 和 wsrv.nl 的实际服务响应来约束实验参数。例如，论文报告 GitHub JPEG 质量因子约为 75，Gravatar 约为 90。

这使工作不再是简单的“测试扰动是否能抵抗 JPEG 压缩”，而是试图建立一个由 Web 基础设施决定的威胁模型。

**评审判断**：这是有意义的系统性问题定义。若能真正建立现实采集路径与实验结果之间的联系，会成为论文最有说服力的贡献。

### Strength 2：Same-identity baseline 是有价值的方法论改进

第 6.1 节给出了一个值得关注的发现：

| 比较方式 | FSMG 的 Identity Similarity Gap |
| --- | ---: |
| 不同身份划分的 clean baseline | 0.124 |
| 全体身份汇总的 clean baseline | 0.084 |
| 同身份 clean baseline | 0.042 |

结果显示：不匹配的身份集合可能使保护效果看起来放大约 2–3 倍。这个发现具有超越具体方法的意义，因为人脸个性化生成天然受到身份难度的影响。

但应谨慎区分：当前结果证明了**在作者的身份划分下，baseline 选择造成明显偏差**，尚不能据此断言整个领域的已发表结果普遍被放大三倍。

### Strength 3：没有将所有生成模型混为一谈

论文分别考察：

- **DreamBooth-LoRA**：基于 fine-tuning 的身份个性化。
- **IP-Adapter-FaceID**：基于身份嵌入的 zero-shot customization。
- **InstantID**：另一种 zero-shot 身份生成方案。

不同 reader 的响应存在差异。论文也明确区分了模型无法恢复身份与输入图像本身遭到破坏两种情况。

作者在附录披露实验实施错误及修复过程，也体现出透明性；但透明披露不能替代对受影响主实验的重新验证。

---

## 三、主要问题（Major Weaknesses）

以下问题按对录用决定的影响排序。

### M1. 主实验存在尚未完全修复的预处理混杂因素

**严重程度：Critical；最可能直接导致拒稿。**
**证据位置：Appendix A.1，PDF 第 10 页，“Gallery ingestion”。**

论文承认，原始实验中：

- Clean 图像先进行中心裁剪，再进入生成模型。
- Protected 图像没有执行相同的裁剪，而是直接将 CelebA 的 178×218 图像缩放为方形。
- 虽然释放的代码已经修复这个问题，但主要结果表格仍保留原始实验数据。

作者认为，这种几何偏差不会人为制造不同 tier 之间的退化趋势，因为它与 tier 无关。

**这一解释不足以作为充分证据。**

第一，文章最强调 same-identity matched evaluation，但仅匹配 identity 并不够。输入图像的裁剪、纵横比和读取过程也必须一致，否则存在系统性混杂。

第二，即使几何处理差异对所有 tier 都存在，其影响也不一定是常数。裁剪与压缩、缩放、embedding extraction 之间可能发生非线性交互，从而改变每个 tier 的 gap。

因此，无法仅凭“偏差与 tier 无关”推断 Retention Ratio 不受影响。

> **审稿人可能提出的问题**：How can the authors claim a fair identity-matched evaluation when the clean and protected galleries follow different preprocessing pipelines?

**必须修改**：用完全一致的预处理重新运行主要 clean/protected 对照，重算 Table 2、Table 3、Figure 2 及统计检验。原始错误数据可以保留在附录作为审计记录，但不能继续作为核心结论的依据。

**如果只来得及修改一个问题，应优先解决这一项。**

### M2. “统计不显著”并不能证明“防御失效”

**严重程度：Critical；核心结论存在推断过度。**
**证据位置：PDF 第 6–7 页，Figure 2、Table 3 与 Section 6.2。**

论文的中心结论是：没有方法在 signal-preserving tiers 下保留 Holm-corrected statistically significant gap。

但 Table 3 实际给出了：

| 变换 | FSMG 的 RR | 相对于 T0 的 Gap 损失 |
| --- | ---: | ---: |
| JPEG-85 | 0.720 | 28.0% |
| WebP-80 | 0.832 | 16.8% |
| Canvas T2 | 0.624 | 37.6% |
| Super-resolution T4 | 0.837 | 16.3% |

这些结果可以支持“保护出现退化”，但 **RR = 0.72 表示点估计仍保留了 72% 的原始 gap，并不意味着 gap 已经归零。**

与此同时，作者自己报告：

- 主实验的配对身份数量约为 18–22。
- 80% power 下的最小可检测 gap 约为 0.03–0.08。
- 实际 gap 本身约为 0.03–0.05。

这意味着实验检测能力与所研究的效应处于相近尺度。因此：

\[
p > 0.05 \;\not\Rightarrow\; \Delta(T) = 0.
\]

Holm 校正后的不显著，只能说明当前数据没有提供足够强的统计证据来支持非零 gap，不能直接证明防御效果不存在。

这里有两个不同的问题：

1. **防御是否仍然有效？** 需检验 \(\Delta(T)\) 是否大于有实际意义的阈值。
2. **采集变换是否削弱了防御？** 需检验 \(\Delta(T_0)-\Delta(T)\) 的大小及置信区间。

论文目前过度依赖第一个问题的不显著性，推导第二个问题以及“collapse”的结论。

**必须修改**：为每个 tier 报告配对的绝对 gap、95% 置信区间、RR 置信区间，以及 T0 到该 tier 的 gap 变化。若想证明保护已经降低到实际无用，需要预先定义有意义的最小效果阈值，采用适当的等效性检验或其他以效应大小为中心的统计框架，而不是仅使用不显著性。

### M3. 缺少最相关的强防御基线，导致“Collapse”结论难以泛化

**严重程度：Critical；Baseline coverage 不足。**
**证据位置：Sections 5.1、5.3、5.4。**

稿件主要评测 FSMG-style、ASPL-lite，以及在 FSMG 上添加 JPEG-aware retraining 的 FSMG-J。

但已有研究直接关注压缩鲁棒性、zero-shot 身份保护或 purification resistance。前次评审提出需要重点对照的例子包括：

- **IDProtector**（CVPR 2025）：面向身份生成方法，并研究几何及压缩变换下的鲁棒性。
- **GAP-Diff**（NDSS 2025）：研究压缩之后的 diffusion-based facial customization 防御。
- **AntiPure**（ICCV 2025）：研究经过 diffusion purification 后仍保持保护效果的扰动。

这些代表性工作及其适用设置应在投稿前逐一核对，确认实验预算和威胁模型具有可比性。

稿件引用了部分 JPEG-robust 工作，却没有将这些方法作为主要实验比较对象。这将引发一个非常直接的问题：

> Are the observed failures fundamental to anti-customization protections, or specific to relatively weak and outdated baselines?

尤其是 FSMG-J 的实验结果不足以回答这个问题。它只是一个 JPEG-aware 改造版本，不能代表已有专门设计的鲁棒防御方法。

ASPL-lite 也属于简化实现，不应在缺少实现一致性验证的情况下，将其表现直接推广至完整 ASPL 或后续方法。

**必须修改**：至少纳入两类更强的基线——JPEG/resize-robust 方法，以及 purification-robust 或 zero-shot-aware 方法。优先使用公开官方实现，并统一真实像素尺度下的扰动预算。

否则，应显著收窄结论，例如从“face protections collapse”改为“tested T0-optimized defenses exhibit acquisition sensitivity”。

### M4. “Real-Web Image Acquisition” 的实证支撑仍然不够

**严重程度：High；Web 真实性和外部有效性不足。**
**证据位置：Sections 3.4、5.3、7.4。**

本文确实进行平台行为探测，但核心身份保护实验仍然使用软件模拟的图像变换。

存在至少四个限制：

1. 四个 HTTP 服务的 JPEG 参数测量并不等于完整的真实 Web 获取链路。浏览器 DPR、CDN 裁剪、图像尺寸、页面布局、截图、上传路径都会影响最终像素。
2. 论文提出 T0–T6 acquisition funnel，但主要实验分别独立应用六种单步操作。真正的复合链路实验只在附录的六身份子集上报告。
3. CelebA 原始图像分辨率较低、相对规范化，难以代表社交平台中复杂的人脸尺寸、姿态、多人构图与压缩历史。
4. T3、InstantID 以及 Stage C 的关键修复结果均主要依赖六身份 pilot，外部有效性有限。

**关键建议实验**：同一张获得合法使用授权的图像，分别通过真实 Web 平台上传和获取，以及 ScrapeBench 软件模拟路径处理，比较两者的像素差异、身份保真度和最终攻击结果。

这能回答核心问题：ScrapeBench 测到的是现实 Web 带来的脆弱性，还是某套人工构造变换带来的脆弱性？

没有这一步，论文可以称为 *Web-inspired acquisition benchmark*，但以 *Real-Web Image Acquisition* 为标题仍然偏强。

### M5. ARCP 的证据不足以支撑一项成熟的新防御贡献

**严重程度：High。**
**证据位置：Section 4、Section 6.4、Tables 2–5。**

ARCP 的设计包括低频扰动、纹理感知的 amplitude allocation、Expectation over Transformation（EOT）以及身份 embedding repulsion。这些组合具有一定合理性，但大多数构成要素并非全新。若将 ARCP 作为独立算法贡献，审稿人会要求说明每一部分具体带来的收益。

| Reader | ARCP 实验结果 | 审稿判断 |
| --- | --- | --- |
| InstantID | JPEG-85 下 RR=0.97；T2 下 RR=1.18 | 仅六身份 pilot，统计证据不足 |
| IP-Adapter-FaceID | T0 配对 gap 约为 0.031；主要实验中 gap 很小 | 没有证明有效跨模型迁移 |
| DreamBooth-LoRA | 正文声称覆盖 Stage B，但 Table 5 未给出 ARCP 行 | 缺少直接证据 |

ARCP 在 InstantID 实验中的 p 值分别为 0.094（T0）、0.062（JPEG-85）和 0.031（T2）。其中 T2 的 0.031 未经过多重比较校正，论文也承认相关结论无法通过 Holm correction。

所以“ARCP survives JPEG and canvas rendering”目前最多是**六身份样本上的积极趋势**，不是已经确认的鲁棒性优势。

另需澄清：第 5 节说用于选择超参数的六身份 pilot 不进入报告统计，第 6.4 节又报告六身份 forging pilot 的 ARCP 结果。作者应明确是否为两组互不重叠的身份，否则存在调参和测试数据混用的风险。

同样，Section 5.3 描述了四种方法的 InstantID grid，但附录 Table 4 仅列出 Clean、FSMG 和 FSMG-J，没有展示 ARCP 结果。

**建议**：要么将 ARCP 明确降级为 proof-of-concept，要么补充独立测试身份上的完整评估，并加入低频参数化、纹理分配、EOT 和 embedding objective 的消融。还必须证明原有 fine-tuning protection 没有被牺牲。

### M6. face-consent.txt 的威胁模型与论文目标不完全一致

**严重程度：Medium–High。**
**证据位置：Sections 3.5、7.3。**

face-consent.txt 将保护从图像像素转移到机器可读的同意声明，是一个有趣的 Web-oriented 方向。

然而，论文称其可以在 acquisition funnel 中持久存在，需要更谨慎。在图像被截图、重新上传、裁剪或转发后，原站点 manifest 与新图像之间的关联可能丢失；恶意爬虫也可以选择忽略 manifest。

因此，该方案解决的是**愿意遵守协议的采集者如何识别同意状态**，而不是**恶意采集者如何被技术性阻止**。两者的威胁模型不同。

还应讨论：谁有权为含有他人面部的照片声明 consent、如何处理多人的照片、以及撤销授权后已复制图像如何追踪。

**建议**：将 face-consent.txt 表述为标准化提案或系统原型，而不是已经验证的 durable fix，并补充端到端协议评估。

---

## 四、其他技术性问题（Minor / Additional Concerns）

| 问题 | 证据与影响 |
| --- | --- |
| 扰动预算不完全一致 | Appendix A.5 中，FSMG 等方法的 16/255 定义在 [-1,1] 空间，random control 则在 [0,1] 空间。实际像素幅度相差两倍，不适合直接做严格的同预算比较。 |
| PSNR 需要核对 | 如果在同一像素网格上严格执行 ±8/255 的扰动上限，理论上 PSNR 不应低于约 30.1 dB，而文中报告 FSMG 为 28.1 dB。需要澄清是否存在额外重采样、编码或不一致的图像比较过程。 |
| 评估指标较单一 | ArcFace identity similarity 和固定阈值 τ=0.30 是主指标。建议补充独立人脸识别模型、输入图像质量和生成质量评估。 |
| 缺少直观生成结果 | 全文主要是指标与曲线，缺少生成图像对照示例。可使用授权或合成人脸，展示输入质量相当时是否真正恢复身份。 |
| Cost ledger 有简化 | 防御生成的 GPU 时间与压缩的 CPU 时间可以比较增量成本，但不能直接等同完整攻防成本；应区分预处理、训练和生成成本。 |
| 可复现材料访问不清晰 | Appendix A.2 声称发布代码和日志，但 PDF 中未见可验证的匿名仓库入口。应让审稿人能访问环境配置、脚本、模型和结果复现材料。 |
| Stage B 的基线不匹配 | 第 6.3 节 DreamBooth-LoRA 使用 cross-identity comparison，与本文主张的 matched baseline 标准不一致。相关结果只能作方向性分析。 |

对于 benchmark 论文，**实验协议本身必须比被评估的方法更加经得起审查。**

---

## 五、创新性与定位：论文真正的新意是什么？

| 贡献 | 创新性判断 |
| --- | --- |
| Web Acquisition Gap 的问题定义 | 有价值，但建立在已知的变换脆弱性问题之上 |
| 七层 acquisition funnel | 较好的系统组织与 benchmark 设计 |
| Same-identity paired evaluation | 合理且重要，但不是全新的统计原理 |
| Retention Ratio | 实用的归一化指标，理论创新有限 |
| ARCP | 现有技术组合，尚未证明独特优势 |
| face-consent.txt | 有 Web 研究特色，但验证不足 |

在相关工作中，需特别与研究真实图像变换下保护扰动可靠性的论文清晰区分。现有研究已涉及 JPEG 消除扰动、变换鲁棒防御和 purification 等问题，因此 ScrapeBench 的贡献不能仅是“再次发现 JPEG 会削弱扰动”。

**最有希望成立的独特价值**是：建立一个与实际 Web 分发过程相关、跨攻击模型、控制身份匹配与质量退化的统一评估协议。

把这件事做好，足以形成具有竞争力的 WWW evaluation paper；没有必要同时宣称提出突破性新攻击、强鲁棒新防御和完整的 Web consent solution。

---

## 六、按优先级排序的修改计划

### P0：必须在投稿前解决

- 统一 clean/protected preprocessing，并重新运行核心实验。
- 重新计算配对 gap、RR、置信区间和 Holm 检验。
- 校正扰动预算单位，统一实际像素扰动幅度。
- 使主实验表格与最终修复后的评估协议完全一致。

**这是论文可信度的底线。**

### P1：最能提高录用竞争力

- 增加至少一个强 JPEG-robust baseline 和一个 zero-shot-aware baseline。
- 用真实 Web 上传—获取链路进行端到端验证，并与模拟链路对照。
- 为 DreamBooth-LoRA 建立 matched-identity 对照。
- 强化统计功效分析，重点报告可估计的效应大小及置信区间，而非仅以显著性判定“失效”。

**这组实验直接回应“结论是否具有广泛性”的疑问。**

### P2：写作与贡献重新聚焦

- 弱化 *collapse* 的绝对性表述。
- 将 ARCP 定位为探索性参考方案，除非有额外强证据支持算法贡献。
- 将 face-consent.txt 定位为协议讨论或系统原型。
- 在正文允许页数内完整展示核心验证结果。
- 提供匿名可审查的代码、实验日志和结果材料。

**减少不必要的审稿争议，把篇幅留给最强证据。**

### 建议更换论文标题

当前标题：

> *ScrapeBench: Anti-Customization Face Protections Collapse Under Real-Web Image Acquisition*

最危险的词是 **Collapse**。它诱导审稿人期待几乎所有现有保护在现实采集下都基本失效，但当前主要结果尚达不到这一证明强度。

建议标题：

> **ScrapeBench: Measuring the Web Acquisition Gap in Face Anti-Customization**

新标题保留 Web Acquisition Gap 和 benchmark 两个最有辨识度的贡献，同时将论证责任从普遍失效转移到可量化的鲁棒性差距。

如果后续完成强 baseline 和真实 Web trace 实验，并得到具有足够统计功效的接近零保护效果证据，再使用更强的标题会更有说服力。

---

## 七、WWW 2027 投稿与格式注意事项

> 本节是此前审稿意见中的会务提醒，**日期及页数细则务必以 WWW 2027 官方 Research Track CFP 和最终投稿系统为准**。

此前评审所列时间节点为：

| 事项 | 日期 |
| --- | --- |
| 摘要截止 | 2026 年 10 月 18 日 |
| 全文截止 | 2026 年 10 月 25 日 |

此前评审按 Research Track 正文最多 8 页、其余页面用于参考文献及附录的规则进行格式判断。当前 PDF 共 12 页，但并不意味着前 8 页的内容已经足够自洽。

需要特别检查：

1. 目前 Table 4 被排到 PDF 第 12 页，却在第 7 页的关键论证中引用。核心证据应尽量放在正文中。
2. 页眉与 ACM Reference 仍出现 `Conference'17`、旧会议地点及占位 DOI，应按 2027 模板清理。
3. 提供可匿名访问的代码、实验日志和复现入口。
4. 确认正确的 Research Track 及其审稿范围，不要混淆不同类别的征稿和出版规则。

---

## 八、模拟审稿人最终意见（英文）

**Overall Recommendation: Weak Reject (4/10)**

**Summary of assessment**

This paper addresses an important and timely Web privacy problem and proposes a useful evaluation perspective for face anti-customization defenses. The acquisition-oriented benchmark and identity-matched reporting methodology are potentially valuable to the community.

However, the empirical evidence is currently insufficient to support the paper's broad collapse claims. The retained gaps are often nonzero, statistical power is limited, major comparisons omit stronger robustness-oriented defenses, and an acknowledged preprocessing inconsistency remains in the primary results. The proposed ARCP defense and consent mechanism are also evaluated less comprehensively than their claimed contributions suggest.

**Recommendation**

I would be willing to reconsider a revised version with corrected primary experiments, stronger contemporary baselines, and more conservative conclusions. In the current version, I would lean against acceptance.

---

## 九、最终建议

这篇工作的最佳定位是**一篇揭示现有评估协议缺陷、提出 Web 场景鲁棒性评测方法的 benchmark paper**，而不是以“彻底攻破现有保护方法”为中心的攻击论文。

前者的成功标准是评估协议严谨、数据具有代表性、结果可复现；后者则必须证明足够强的现有防御在现实环境下确实失效。

现在最能让审稿人改变判断的，并不是再增加一个 T6 operator 或设计一个更复杂的 ARCP，而是提供一张**没有混杂因素、包含强基线、同时展示绝对 gap 与置信区间**的核心结果表。

**若距离全文截止只能完成一轮关键修改，建议先重做 Table 2 / Table 3 对应的核心实验，再同步重写 Abstract、F1/F2 和 Conclusion。**

### 建议下一步

以 P0 修改清单为主线逐项核对代码与实验结果；在确认主表结果可信后，再决定是否需要扩展 P1 的强基线和真实 Web 链路实验。
