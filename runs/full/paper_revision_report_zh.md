# ScrapBench 补充实验与论文修改报告

生成时间：2026-10-13。最终完整性：InstantID 72/72，修复版 T3 18/18，修复版 Stage C 18/18。

## 1. 审计与修复

- InstantID 的批量 prompt/embedding 数量不匹配已修复；最终协议统一为 30 denoising steps。
- 最早 `clean/celeb00025/T0` 的 25 步冒烟结果已于 2026-10-13 08:25 强制重跑为 30 步：均值从 0.3569 变为 0.3566，结论不变。
- T3 人脸裁剪的 margin 语义已修正。旧实现把每边扩张 0.35 错写成总宽高乘 1.35；修复后 clean control 能正常工作。
- Stage C mixing 已改成同身份 clean-source mixing，避免混入其他身份；`purify50` 现在真正执行强度 0.5 的 img2img，而非沿用错误路径。
- 结果按 append-only CSV 的最新成功行去重。执行失败行不再被当作完成。
- 旧报告器的 NumPy `trapezoid` 和缺失 `tabulate` 兼容问题已修复；严格分析器再次确认三组实验全部完整。

## 2. 指标口径

由于部分生成图没有可检测人脸，不能只报告一个均值。本报告同时给出：

- Conditional ID：只在检测到人脸的生成图上计算 ArcFace 相似度；
- Detection：生成图的人脸检测率；
- Unconditional ID：检测失败按 0 计的总体身份泄露近似值；
- Success：ArcFace 相似度达到阈值 0.30 的比例。

T5 尤其必须同时报告这四项，否则会把“生成图被破坏到检测不到脸”误写成“防御仍然有效”。

## 3. InstantID：6 身份 × 3 方法 × 4 层级

| 方法 | 层级 | Conditional ID | Detection | Unconditional ID | Success |
|---|---:|---:|---:|---:|---:|
| clean | T0 | 0.514 | 80.0% | 0.406 | 78.3% |
| clean | JPEG-85 | 0.541 | 76.7% | 0.413 | 76.7% |
| clean | T2 canvas | 0.547 | 61.7% | 0.336 | 61.7% |
| clean | T5 img2img-30 | 0.256 | 50.0% | 0.139 | 26.7% |
| FSMG | T0 | 0.276 | 63.3% | 0.178 | 28.3% |
| FSMG | JPEG-85 | 0.262 | 65.0% | 0.182 | 21.7% |
| FSMG | T2 canvas | 0.277 | 66.7% | 0.194 | 35.0% |
| FSMG | T5 img2img-30 | 0.101 | 6.7% | 0.007 | 0.0% |
| FSMG-J | T0 | 0.286 | 55.0% | 0.171 | 33.3% |
| FSMG-J | JPEG-85 | 0.277 | 51.7% | 0.153 | 26.7% |
| FSMG-J | T2 canvas | 0.291 | 60.0% | 0.178 | 31.7% |
| FSMG-J | T5 img2img-30 | 0.115 | 3.3% | 0.004 | 0.0% |

以检测失败记 0 的 paired gap（clean − protected）为：

| 方法 | T0 | JPEG-85 | T2 | T5 | RR(J85/T2/T5) |
|---|---:|---:|---:|---:|---:|
| FSMG | 0.228 | 0.232 | 0.142 | 0.132 | 1.018 / 0.624 / 0.578 |
| FSMG-J | 0.235 | 0.260 | 0.159 | 0.135 | 1.108 / 0.677 / 0.574 |

主要解释：

1. InstantID 下存在实质性的 protected-clean 差异，不能再把所有零样本攻击概括为“基本不受影响”。FSMG 的 T0 success 从 clean 的 78.3% 降至 28.3%，unconditional ID 从 0.406 降至 0.178。
2. JPEG-85 没有削弱差异；T2 后差异仍保留约 62%--68%。因此该读者上的曲线与标准 IP-Adapter-FaceID 不同，支持“攻击器特异性”，但不支持“更强读者不继承残余保护”的强表述。
3. T5 的极低 protected 分数主要伴随检测率从 clean 50.0% 降到 FSMG 6.7%、FSMG-J 3.3%。这是图像/人脸可检测性崩溃与残余保护共同作用，不能仅解释为防御保持。
4. FSMG-J 相对 FSMG 没有可靠改进。两者的直接 paired Wilcoxon 检验在所有层级与指标上均不显著（双侧 p >= 0.4375）；保留“JPEG-aware retraining 为 null result”的结论。
5. 6 身份下各层级 clean-protected 的未校正双侧 Wilcoxon p 多为 0.03125--0.0625；对 8 个 InstantID 比较做 Holm 校正后没有一项能在 0.05 下显著。因此应写成强方向性证据/扩大后的 pilot，而不是总体人群结论。

与论文原单身份 probe 比较：新 clean 条件均值在 T0/J85/T2 分别高 0.054/0.081/0.117；新 FSMG 分别变化 -0.084/-0.068/+0.047。单身份原结果的方向并非完全错误，但幅度明显受身份选择影响。

## 4. 修复版 T3 agent face-crop

| 方法 | Conditional ID | Detection | Unconditional ID | Success |
|---|---:|---:|---:|---:|
| clean | 0.376 | 81.7% | 0.308 | 61.7% |
| FSMG | 0.329 | 76.7% | 0.254 | 43.3% |
| FSMG-J | 0.328 | 78.3% | 0.258 | 45.0% |

修复后 clean 不再坍缩，说明旧 T3 的 25/27 无结果确实是 harness defect。FSMG 与 FSMG-J 的 unconditional paired gap 分别为 0.054 和 0.051；每个身份方向都为 clean > protected，未校正双侧 Wilcoxon p=0.03125。两项一起校正后不低于 0.05，仍应按小样本 pilot 表述。

论文不应再写“T3 因完整性失败被排除且未修复”。建议把修复版结果放主文补充表或附录，并明确它显示的是一个较小但一致的残余 gap，而不是旧版接近零的伪结果。

## 5. 修复版 Stage C

| 条件 | 原无效均值 | 新 Conditional | Detection | 新 Unconditional | Success |
|---|---:|---:|---:|---:|---:|
| mix20 | 0.042 | 0.097 | 60.0% | 0.059 | 0.0% |
| mix50 | 0.022 | 0.094 | 63.3% | 0.062 | 5.0% |
| purify50 | 0.078 | 0.063 | 65.0% | 0.045 | 0.0% |

修复后的 mix20/mix50 conditional ID 明显高于旧错误结果，但 clean-source 比例从 20% 增至 50% 并未产生单调恢复；purify50 仍最低。检测率为 60%--65%，因此不能把这些低均值全部归因于“没有脸”，但 success 几乎为零也表明当前 400-step、6 身份 pilot 中 DreamBooth 攻击总体很弱。

Stage C 目前缺少一个在完全相同身份、相同训练代码下重跑的纯 clean/纯 FSMG 对照，故不宜用它声称 mixing 或 purification 已被证明有效/无效。可将其作为修复后的探索性结果，并把 matched endpoints（mix0、mix100、purify0）列为下一轮最优先实验。

## 6. 对 F1--F5 的影响

- F1：基本不变。新结果再次显示身份差异很大，且 n=6 经多重校正后不足以给出显著性强结论。
- F2：需要收窄。应从“零样本提取器基本不受影响”改为“保护高度依赖攻击器；IP-Adapter-FaceID 上影响较弱，但 InstantID 上观察到较大 protected-clean gap”。机制层面的 fine-tuning vs embedding-injection 二分过于粗糙。
- F3：得到更强的指标层支持。T5 同时大幅降低检测率，必须把身份泄露减少与输出破坏分开；但不要把所有 T5 差异都归因于破坏，因为 conditional ID 也下降。
- F4：前半句“FSMG-J 没有可测改进”被支持；后半句“更强零样本读者不继承残余保护”应删除或改为“不同零样本读者产生不同幅度和 retention 曲线”。
- F5：不受新实验直接改变；成本结论仍成立，但不能用成本结论代替效果显著性。

## 7. 建议直接修改论文的位置

1. `experiments.tex`：把 Stage A-instant 从“5 身份、仅 1 身份完成”改为“6 身份 × 3 方法 × 4 tiers，30 steps，每格 10 generations”。补充 conditional/detection/unconditional/success 四指标定义。
2. `results.tex` 开头：删除三项均被排除的旧说明；改成 T3 与 Stage C 已修复、InstantID grid 已完成，并说明它们仍是 6 身份 pilot。
3. F2 段落：不要再说 zero-shot reader “essentially unaffected”；明确 IP-Adapter-FaceID 与 InstantID 结果不一致。
4. F4 段落：用 6 身份表替换单身份 `.46/.46/.43` 与 `.36/.33/.23` 叙述；同时给出 detection-failure-zero RR。
5. `appendix.tex` integrity audit：保留旧故障作为审计记录，但增加修复原因、修复时间和修复后完整结果，避免读者以为结果仍缺失。
6. `discussion.tex` 与 `conclusion.tex`：将“zero-shot attackers bypass the mechanism”改成概率性、攻击器特异性的表述，例如“zero-shot injection removes the poisoned-gradient path, but does not guarantee invariance to protected pixels; InstantID still shows a sizable gap.”
7. 局限性：明确 6 身份、10 generations/cell、同一随机种子与 detector-dependent scoring；报告多重校正后不显著，避免把 pilot 写成 population-level proof。

## 8. 可直接替换的英文核心表述

> On a completed six-identity InstantID pilot, FSMG reduced the detection-failure-zero identity score from 0.406 to 0.178 at T0 and the success rate from 78.3% to 28.3%. The paired gap persisted at JPEG-85 (0.232) and retained 62.4% of its T0 magnitude after canvas recapture. This result revises the simpler claim that zero-shot readers are uniformly unaffected: protection is reader-specific even within the embedding-injection family. With only six identities, however, none of the eight protected-clean comparisons survives Holm correction, so we treat the grid as an expanded pilot rather than population-level evidence.

> Repairing the agent-crop geometry restored the clean control (conditional identity 0.376; detection 81.7%), confirming that the earlier near-zero T3 cells were a harness failure. FSMG and FSMG-J showed smaller unconditional gaps of 0.054 and 0.051. We therefore report T3 separately rather than excluding it as an unresolved integrity failure.

> The repaired adaptation path raises mix20 and mix50 conditional scores to 0.097 and 0.094, while purify50 remains at 0.063. Because this pilot lacks matched mix0/mix100 endpoints and attack success remains near zero, it diagnoses the prior implementation fault but does not establish the efficacy of adaptive mixing or purification.

## 9. 下一轮实验优先级

1. 首先增加 InstantID 身份数（至少 20），并使用多个生成 seed；这是决定 F2/F4 是否需要实质改写的最高价值实验。
2. 为 Stage C 加入同身份 clean、FSMG、mix0、mix20、mix50、mix100、purify0、purify50 的完整 matched curve。
3. 对 InstantID/IP-Adapter 同时保存每张图的检测状态与相似度，直接 bootstrap image-within-identity / identity 两层不确定性。
4. 固定并记录 detector 版本和 crop geometry；将 detector failure 作为独立 outcome，而不是静默 NaN。
