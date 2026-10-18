# ScrapeBench 完整技术说明：四身份验证版

> 更新日期：2026-10-17。本文只记录当前保留的论文主线、可复现实验协议和已经核验的事实。历史上协议不一致、实现有误或已显示效果不佳的探索结果不进入本文的结果表，也不作为论文结论。

## 1. 用一句话理解这篇论文

ScrapeBench 研究的不是“给照片加噪声后，某一个模型是否立刻失效”，而是：**用户把受保护的人脸照片发布到 Web 后，照片经过一次常见 Web 操作，拒绝被人脸定制的信号是否仍然有效。**

核心对象有三方：

1. 人发布照片，并可能用抗定制方法保护照片；
2. Web 平台、浏览器或 AI agent 对照片压缩、缩放、截取或重建；
3. 攻击者把获取到的照片交给人脸定制模型，生成该人的新图像。

论文的 Brave New Idea 是把抗定制从“一个文件上的像素属性”改写成 Web 上的 **acquisition contract（获取契约）**：每一种正常的 Web 获取操作都是一条可独立检验的契约条款。如果一张图经过 CDN 压缩后保护消失，责任边界和工程改进点就指向 T1，而不是含糊地说“七级漏斗最后失败了”。

## 2. 当前真正要回答的问题

设身份为 (s)，其公开 gallery 为 (X_s)，保护器为 (D)，发布的保护图为

\[
\widetilde X_s=D(X_s).
\]

Web 单步操作记作 (\phi_k)，人脸定制器记作 (P)，仅用于评价的未保护参考图为 (R_s)。我们成对比较

\[
P(\phi_k(X_s))
\quad\text{和}\quad
P(\phi_k(\widetilde X_s)).
\]

两条分支必须使用同一身份、同一预处理、同一 (\phi_k)、同一 prompt、同一随机种子和同一评分器。这样才能把差异归因于保护方法，而不是数据或裁剪混杂。

当前四身份验证实验只回答三个问题：

1. Clean 分支在每个 T 和每个定制器上是否真的能恢复身份；
2. 各保护器能否在相同条件下降低恢复出的身份相似度；
3. ARCP-Web-v4 是否显示出足够好的效应方向，值得扩展到 40 身份。

四身份结果不能证明总体显著性，也不能支持人口统计或全面 SOTA 结论。

## 3. T0–T6：不是七级串联漏斗，而是七个独立单层实验

每个 T 都直接读取同一张 T0 上传图。主实验中不存在 (T0\to T1\to\cdots\to T6) 的累计链路。

| 层 | 独立操作 | 对应 Web 行为 | 当前实现 |
|---|---|---|---|
| T0 | 原始 512×512 上传图 | 原站文件/直链 | 不变换 |
| T1 | JPEG Q70、4:2:0 | CDN 或平台转码 | Pillow JPEG，短边统一到 512 |
| T2 | 360 CSS 像素、DPR=1 | feed 卡片/缩略图渲染 | canvas 卡片渲染后取回图像区域 |
| T3 | 检测人脸、每侧扩展 35%、WebP 80 | agent 从渲染页面截图并截脸 | 检测器引导裁剪、512 重采样、WebP |
| T4 | Real-ESRGAN ×2、JPEG 92 | 修复/超分服务 | 真实 Real-ESRGAN 权重；失败时禁止静默降级 |
| T5 | SD1.5 img2img，strength=.30 | 生成式编辑或重新发布 | 30 步、空 prompt、guidance=1 |
| T6 | prompt-free SD1.5 重建，strength=.50 | 强重建/净化代理 | 50 步；明确不冒充官方 DiffPure |

T0–T3 是常见 Web 像素路径；T4–T6 是越来越强的模型介入路径。是否“真实”不能靠命名保证，因此每一层还有 Clean 有效性门槛：若 Clean 自身已无法被定制器识别，该列只能报告，不能给防御排名。

## 4. 小规模验证实验的固定设计

### 4.1 数据

- 固定身份：`celeb00001`、`celeb00002`、`celeb00003`、`celeb00004`。
- 每个身份：4 张 gallery（提供给保护器和定制器）+ 2 张 held-out reference（只评分，绝不参与保护或定制）。
- 选择规则：取预先审计 manifest 中前四个有效身份，不根据任何防御结果挑人。
- 扩展池：40 身份、160 张 gallery；已核验 gallery 人脸检测率 96.25%，跨身份平均 gallery-reference ArcFace 相似度 .787。该数据只说明输入可用，不说明防御有效。

### 4.2 保护方法

| 方法 | 角色 | 当前状态 |
|---|---|---|
| Clean | 无保护的成对对照 | 四身份输入完整 |
| GAP-Diff | JPEG 鲁棒抗定制 baseline | 四身份保护图完整 |
| MetaCloak | 鲁棒训练型 baseline | 正在完成四身份官方代码运行 |
| GoodAC | 较新的抗定制 baseline | 四身份保护图完整 |
| ARCP-Web-v4 | 本文独立完整方法 | 四身份保护图完整 |

IDProtector 不进入当前主比较。论文不通过删除失败样本来让 ARCP 获胜；最终表中 ARCP 若没有领先，就必须如实报告并继续改算法，不能改数字。

### 4.3 定制器

当前快速 gate 使用两类 zero-shot 定制器：

- **InstantID**：根据人脸身份特征和结构条件直接生成，不需要逐身份训练；
- **IP-Adapter-FaceID**：把人脸身份 embedding 注入 SD1.5，同样不需要逐身份训练。

DreamBooth 是逐身份微调，成本远高于 zero-shot。它被放在第二 gate：只有四身份 zero-shot 实验显示存在值得扩展的信号后，才对少量身份做 1,000 步 DreamBooth 验证。zero-shot 和 DreamBooth 不混为一张平均表。

### 4.4 四个生成场景

每个 cell 固定生成四张图，每个 prompt 一张：

1. 社交媒体头像；
2. 普通手机自拍；
3. 低光室内社交照片；
4. 有复杂背景的户外旅行照片。

这些“场景”是生成 prompt，不是四种新的 T。T 表示照片在进入定制器前经历的 Web 获取方式，场景表示定制器最终被要求生成什么内容。

### 4.5 实验规模

完整快速矩阵为

\[
4\ \text{身份}\times 5\ \text{方法}\times 7\ T
\times 2\ \text{定制器}\times4\ \text{场景}=1120\ \text{生成图}.
\]

保护图只需每方法 (4\times4=16) 张。GPU 并发上限为 6 个单卡任务；先完成保护，再运行定制和评分，最后自动汇总表格与视觉图。

## 5. ARCP-Web-v4 的完整方法

### 5.1 独立保护器，而不是别的保护器的后处理

ARCP-Web-v4 直接从 clean 图生成保护图，不读取 GAP-Diff、MetaCloak、GoodAC 或 IDProtector 的输出。其扰动由低频网格和全分辨率细节网格组成：

\[
\delta(x)=A(x)\odot\left[(1-\beta)U(z_c)+\beta z_d\right],
\]

\[
\widetilde x=\Pi_{[x-\epsilon,x+\epsilon]\cap[0,1]}(x+\delta(x)),
\]

其中 (z_c\in[-1,1]^{128\times128\times3})，(z_d\in[-1,1]^{512\times512\times3})，(U) 是双线性上采样，(\beta=.55)，最终真实像素预算为 (\epsilon=8/255)。PNG 量化后再次投影，防止四舍五入越界。

### 5.2 纹理感知预算

先用 Sobel 梯度得到局部纹理能量 (t(x))，经过 9×9 平滑并以每张图的 95% 分位归一化：

\[
\widehat t(x)=\operatorname{clip}\left(\frac{\operatorname{AvgPool}_{9}(\|\nabla x\|)}{Q_{.95}},0,1\right),
\]

\[
A(x)=\epsilon_{\min}+(\epsilon_{\max}-\epsilon_{\min})\widehat t(x),
\]

其中 (\epsilon_{\min}=3/255)，(\epsilon_{\max}=8/255)。纹理区使用更多扰动，平坦皮肤区使用更少扰动。

### 5.3 七个可微训练代理

训练端为 T0–T6 各准备一个可微代理 (q_k)：identity、JPEG-Q70、360 像素重采样、带抖动的人脸裁剪、超分 down/up-sharpen 代理、轻度重建 bottleneck、强低通重建 bottleneck。真正评价仍使用表 3 的实现；特别是 T4 使用真实 Real-ESRGAN，T5/T6 使用真实 diffusion pipeline，因此训练代理不能直接“看见答案”。

### 5.4 身份与定制联合目标

令 (c_s) 为 clean gallery 的身份中心，(s_k^D) 和 (s_k^C) 分别为保护与 clean 图经过同一 (q_k) 后对 (c_s) 的相似度。读者违反项为

\[
L_{\mathrm{id},k}=
\operatorname{softplus}_b(s_k^D-m)+
\operatorname{softplus}_b(s_k^D-s_k^C+\rho).
\]

第一项降低保护分支的绝对身份相似度；第二项直接要求匹配的 clean-protected gap 至少为 (\rho)。当前同时使用 FaceNet 和 InstantID 发布的 antelopev2 ArcFace 识别器。人脸关键点仅在 clean 图上检测一次并固定，识别路径保持可微。

扩散破坏项是噪声预测误差 (L_{\mathrm{denoise}})。单层目标为

\[
J_k=L_{\mathrm{denoise}}(q_k(\widetilde x))
-\lambda L_{\mathrm{id},k}
+\gamma\|q_k(\widetilde x)-q_k(x)\|_2^2.
\]

实现以 signed-gradient ascent 最大化 (J_k)：增大定制训练损失，降低身份读者相似度，并鼓励扰动经过该 Web 操作仍有残留。对 (k>0) 的更新还同时加入 T0 身份项，防止以牺牲原始上传图保护为代价获得“Web 鲁棒性”。

### 5.5 最弱层调度

偶数步按 T0–T6 循环，保证每层被同等覆盖；奇数步选择当前配对 gap 指数滑动平均最小的层：

\[
k_t=\arg\min_k\operatorname{EMA}
\left[s_k^C-s_k^D\right].
\]

因此 ARCP 的设计目标是改善当前最弱的契约条款，而不是反复优化最容易的一层。这个机制只是可证伪的设计，不保证实验上必然最强。

### 5.6 ARCP 伪代码

```text
Algorithm ARCP-Web-v4(x, eps=8/255, steps=600)
  compute texture amplitude A(x)
  initialize coarse z_c and detail z_d randomly in [-1, 1]
  compute clean FaceNet/ArcFace identity centroids
  initialize gap_ema[T0..T6] as unseen

  for step = 0 ... 599:
      if step is even:
          k <- cyclic_next(T0..T6)
      else:
          k <- argmin_seen(gap_ema)

      delta <- A(x) * (0.45 * upsample(z_c) + 0.55 * z_d)
      x_adv <- project_pixel_budget(x + delta, x, eps)
      (a_adv, a_clean) <- q_k_pair(x_adv, x)  # identical stochastic parameters

      L_id <- paired FaceNet violation + 2.0 * paired ArcFace violation
      if k != T0:
          L_id <- L_id + 1.5 * direct_T0_identity_violation(x_adv, x)
      L_diff <- diffusion_noise_prediction_error(a_adv)
      L_survive <- mean_square(a_adv - a_clean)
      J <- L_diff - 1.20 * L_id + 0.35 * L_survive

      z_c, z_d <- signed_gradient_ascent(J), clipped to [-1, 1]
      update gap_ema[k] with matched clean-minus-protected similarity

  quantize to PNG and project once more to exact 8-bit eps budget
  return protected image
```

## 6. 指标：每个数字具体表示什么

对生成图 (y)，held-out references 为 (R_s)，身份相似度为

\[
e(y,R_s)=\max_{r\in R_s}\cos(f(y),f(r)).
\]

- **Conditional ISM**：只在成功检测到人脸的生成图上计算平均 (e)。越低通常代表越难恢复身份，但必须同时看 FDFR。
- **End-to-end ISM**：检测失败的图按 0 计入。用于完整系统效果，越低越好。
- **FDFR**：生成图的人脸检测失败率。高 FDFR 不能被偷偷当成身份保护成功，因此单独报告。
- **ISR@0.30**：(e\ge .30) 的生成图比例，检测失败记为 false。越低越好。
- **配对保护 gap**：

\[
\Delta_{k,D,P}=\mathbb E_s[
\mathrm{ISM}_{k,\mathrm{clean},P}(s)-
\mathrm{ISM}_{k,D,P}(s)].
\]

  越大表示保护分支比同身份 clean 分支更难恢复。
- **Retention Ratio**：

\[
RR_{k,D,P}=\frac{\Delta_{k,D,P}}{\Delta_{0,D,P}}.
\]

  它表示 T 层保留了多少 T0 保护 gap，但当 (\Delta_0) 很接近 0 时 RR 不稳定，不能单独解释。
- **质量指标**：真实 8-bit (L_\infty) 和 PSNR。不同官方方法的默认预算可能不相同，因此“官方默认参数表”和“统一 8/255 表”必须分开。

层有效性门槛：匹配的 Clean 分支至少检测到 50% 输出，并且其 end-to-end ISM 至少保留 Clean-T0 的 50%。门槛未过的列标为 `Valid=no`，不进行方法排名。

## 7. 截至 2026-10-17 已核验的结果

### 7.1 保护图完整性与图像质量

以下来自实际 PNG 与 clean 输入逐像素比较，不是估算：

| 方法 | 已完整身份 | 每身份保护图 | 最大实测 (L_\infty) | 平均 PSNR | 可得出的结论 |
|---|---:|---:|---:|---:|---|
| GAP-Diff | 4/4 | 4 | 9/255 | 31.68 dB | 产物完整；属于官方默认预算结果 |
| GoodAC | 4/4 | 4 | 8/255 | 33.45 dB | 产物完整，满足 8/255 |
| ARCP-Web-v4 | 4/4 | 4 | 8/255 | 37.80 dB | 产物完整，严格满足 8/255，当前视觉失真最小 |
| MetaCloak | 4/4 | 4 | 11/255 | 29.76 dB | 保护图完整；官方默认半径为 11，定制评价仍在运行 |

ARCP 满足 8/255 且平均 PSNR 最高；与同为 8/255 的 GoodAC 相比高 4.35 dB。PSNR 仍不等于抗定制效果，必须结合下面的配对结果。

### 7.2 定制结果

新的隔离运行目录为 `runs/web4_validation/`。Clean、GAP-Diff、GoodAC、ARCP-Web-v4 的两种 zero-shot 完整矩阵已经完成，共得到 224 个方法-身份-定制器-T ledger；MetaCloak 的两种定制评价仍在运行。

在通过 Clean 有效性门槛的 11 个“定制器 × T”条件中，ARCP-Web-v4 有 9 个取得最大配对 gap：InstantID 的 T0–T3，以及 IP-Adapter-FaceID 的 T0–T4。两个例外都是 T5：InstantID 由 MetaCloak 领先，IP-Adapter 由 GoodAC 领先。InstantID 的 T4/T6 和 IP-Adapter 的 T6 因 Clean 自身失效而不能排名。

- InstantID：ARCP 在 T0–T3 的 gap 为 .216、.199、.177、.121，四个 95% CI 都不跨 0；T5 只有 .033，MetaCloak 为 .118，GoodAC 为 .108。
- IP-Adapter-FaceID：ARCP 在 T0–T4 的 gap 为 .148、.140、.180、.165、.073，五个 95% CI 都不跨 0；T5 为 .047，GoodAC 为 .069。
- ARCP 的 RR：InstantID T1–T3 为 .918/.818/.558；IP-Adapter T1–T4 为 .951/1.218/1.116/.494。T5 的 RR 明显下降，是当前最清楚的弱点。

当前快照已经生成：

- `web40_full_summary.csv`：每个方法 × 定制器 × T 的完整数值；
- `web40_full_summary.md`：可直接阅读的大表；
- `web40_by_scenario.csv`：四个场景分别统计；
- `visuals/*.png`：固定 `celeb00001`、同 prompt/seed 的 Fig.-8 风格可追踪视觉面板；
- `protection_quality.csv`：逐身份真实扰动预算和 PSNR。

可以说 ARCP 在当前四身份快照的 9/11 个有效条件中点估计领先，并且这 9 个 gap 的区间均不跨 0；不能把四身份结果写成总体 SOTA 或人口结论。历史 ARCP 版本、旧单 prompt、几何预处理不一致、累计漏斗及旧 T4 运行均不进入当前结论。

## 8. 如何阅读最终大表

每个定制器应分别看一张表，不要先跨定制器平均。建议顺序：

1. 先看 `Valid`。若为 `no`，这一 T 的 clean 攻击已经坏了，不排名；
2. 再看 Clean 的 E2E ISM，确认定制器确实恢复身份；
3. 对每个保护方法看 paired gap，越大越好；
4. 同时看 95% CI。四身份 CI 会很宽，主要看效应方向和是否存在明显失败层；
5. 看 FDFR，避免把检测器失败误当保护；
6. RR 只回答相对 T0 的保留率，不代替绝对 gap；
7. 最后结合 PSNR/L∞，确认优势不是靠更大的噪声预算换来的。

ARCP 进入 40 身份扩展的建议 gate：两个定制器的 Clean-T0 都有效；ARCP 不出现系统性负 gap；并且在有效 T 中多数层的 paired gap 至少不弱于最强 baseline。四身份不足以做“统计显著 SOTA”判断。

## 9. 实验执行伪代码

```text
fix identities, gallery/reference split, prompts and seeds

for defense in [Clean, GAP-Diff, MetaCloak, GoodAC, ARCP-Web-v4]:
    generate exactly four 512x512 gallery images per identity
    audit completeness, L_inf and PSNR

parallel with a bounded seven-task GPU array:
    for reader in [InstantID, IP-Adapter-FaceID]:
        for defense:
            for identity:
                for T in [T0, T1, ..., T6]:
                    transformed_gallery <- T(protected_gallery)  # always from T0
                    generate one output for each of four fixed prompts
                    score against held-out references
                    save image + per-sample JSONL ledger

compute clean validity gates
compute conditional/e2e ISM, FDFR, ISR, paired gap and RR
bootstrap over identities, never over individual generated images
build tables and fixed-identity visual panels
if feasibility gates pass:
    expand the unchanged protocol to the pre-audited 40 identities
    then run the separate DreamBooth gate
```

## 10. 代码地图

| 内容 | 文件 |
|---|---|
| 主实验配置与四个 prompt | `configs/web40_single_intervention.yaml` |
| T1 JPEG | `scrapebench/funnel/transcode.py` |
| T2 canvas/feed | `scrapebench/funnel/browser.py` |
| T3 agent 截图/人脸裁剪 | `scrapebench/funnel/agent_capture.py` |
| T4 Real-ESRGAN | `scrapebench/funnel/restore.py` |
| T5/T6 diffusion 重建 | `scrapebench/funnel/regenerate.py`、`mixpool.py` |
| ARCP-Web-v4 | `scrapebench/protection/arcp.py` |
| Stage A 定制、保存图和逐样本 ledger | `scrapebench/runner/stage_a.py` |
| GAP-Diff/MetaCloak/GoodAC 官方代码包装 | `scripts/run_official_web40_protector.py` |
| 指标汇总 | `scripts/summarize_web40.py` |
| 视觉面板 | `scripts/make_web4_visuals.py` |
| 保护质量审计 | `scripts/audit_web4_protection.py` |
| 四身份并行评价任务 | `slurm/web4_eval.sbatch` |
| MetaCloak 评价任务 | `slurm/web4_metacloak_eval.sbatch` |
| 自动汇总任务 | `slurm/web4_summary.sbatch` |

## 11. 当前服务器任务与自动依赖

全部实验已经完成。MetaCloak 的尾部任务 `141727_[0-3]` 和最终汇总 `141731` 均以退出码 0 完成；最终表包含 5 个分支、2 个定制器、7 个独立 T 和 4 个身份，共 280 个可审计 ledger。

## 12. 论文现在可以与不可以说什么

现在可以说：

- ScrapeBench 提出了独立单层、成对、带有效性门槛的 Web 获取评价协议；
- T0–T6 已有明确可执行实现，T4 不会静默退化成普通插值；
- ARCP-Web-v4 是 clean-to-protected 的独立保护器，严格满足实测 8/255；
- ARCP 当前四身份保护图的平均 PSNR 为 37.80 dB；
- ARCP 在当前 11 个可排名条件中的 9 个取得最大配对 gap；
- 所有最终生成图和分数都有逐样本 ledger，可追踪到身份、T、prompt 和 seed。

现在不可以说：

- ARCP 在所有七个 T、所有定制器上都最强；T5 明确不是；
- 四身份结果证明统计显著或能代表人群；
- RR 不显著等于保护“完全崩溃”；
- T4–T6 等同所有真实平台；
- 视觉图看起来不像本人就等于定量保护成功。

真正有说服力的论文路径是：先用四身份快速发现协议或方法问题；通过 gate 后冻结代码和超参数，再扩展到 40 身份；最终只按真实结果收窄或加强论文结论。

## 13. T5/T6 后续修正（2026-10-17）

T6=.50 下，InstantID 的 Clean E2E-ISM 从 T0 的 0.318 降到 0.112（保留 35%），IP-Adapter 从 0.408 降到 0.178（保留 44%），均低于预注册的 50% Clean-retention gate。因此这说明强重建本身已使当前定制器难以恢复身份；该层可作为压力测试保留，但不能把 protected 的低分归功于某个防御器。现已提交 `141740`，只用 Clean 在 strength 0.30/0.35/0.40 上校准最强且仍可攻击的 T6，绝不根据防御胜负选择强度；`141751` 自动汇总。

T5 是有效层，ARCP-v4 的确落后：InstantID gap 为 0.033，而 MetaCloak 为 0.118；IP-Adapter gap 为 0.047，而 GoodAC 为 0.069。原因是 v4 的训练代理主要是像素低通 bottleneck，而评价是实际 SD img2img，存在代理失配；同时 55% 细节分支更容易被生成式重建抹去。

当前论文与公开代码冻结在 ARCP-Web-v4。后续开发候选只有在新的预注册身份上确认后，才允许替换这一正式版本。
