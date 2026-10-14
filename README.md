# ScrapeBench

**Do Anti-Customization Defenses Survive the Real Web?**

ScrapeBench 是首个把**真实 Web 获取漏斗**（平台转码 → 浏览器/Agent 截图 → 超分修复 → 扩散再生 → 自适应攻击）作为一等攻击面的抗定制（protective perturbation）评测基准。

核心发现目标：现有防御（Anti-DreamBooth、MetaCloak、SimAC 等）在"干净图片 + 实验室变换"上自证有效；ScrapeBench 沿漏斗层级 T0→T6 测量保护率的**崩塌曲线**。

## 威胁模型（漏斗层级）

| 层级 | 名称 | 说明 |
|---|---|---|
| T0 | raw | 无变换（全部已有工作的默认设置） |
| T1 | transcode | 平台转码：JPEG 质量扫描 q∈{95,85,75,65}、resize、WebP |
| T2 | browser | 浏览器信息流截图（Playwright；无浏览器时用 canvas 回退） |
| T3 | agent | Agent 整页抓取 + 人脸区域裁切 |
| T4 | restore | 超分修复（Real-ESRGAN，或 Lanczos+锐化回退） |
| T5 | regenerate | 扩散再生：img2img (s∈{0.3,0.5}) / DDIM 反演重建 |
| T6 | adaptive | 混池攻击（clean:perturbed 混合训练）+ 净化后训练 |

## 目录结构

```
scrapebench/
  funnel/        T0–T6 漏斗实现
  metrics/       ArcFace ID-sim、KID、PSNR、统计检验
  protection/    防御方法（clean/random 对照 + FSMG/ASPL-lite 重实现 + 官方结果挂钩）
  attack/        DreamBooth-LoRA（微调式）+ IP-Adapter-FaceID（zero-shot）
  runner/        Stage A/B/C 实验编排（可断点续跑）+ 报告生成
  auto_push.py   实验结束自动把结果推送到 GitHub
scripts/         数据准备、一键运行、部署脚本
configs/         smoke / stage_a / stage_b / stage_c 配置
vendor/          第三方组件（见 ATTRIBUTION.md）
```

## 快速开始（实验机）

```bash
bash scripts/setup_lab.sh          # 依赖安装
python scripts/prepare_data.py --source kaggle --data-root data --n-ids 40 --per-id 8
bash scripts/run_smoke.sh          # 2 身份端到端烟测
bash scripts/run_all.sh            # Stage A (GPU0) + Stage B (GPU1) + Stage C，结束自动推 GitHub
```

结果自动回传：`run_all.sh` 在每个 Stage 结束、以及进程退出（含异常）时调用 `scrapebench/auto_push.py`，
将 `runs/*/results*.csv`、`report/`、`logs/` 提交并推送到 GitHub（PAT 从 `~/.scrapebench_pat` 读取，600 权限）。
另有 `scripts/watch_and_push.sh` 每 30 分钟增量推送一次中间结果。

## 指标

- **ID-sim**：生成图 vs 参照集的 ArcFace 余弦相似度（InsightFace buffalo_l）
- **P@τ**：ID-sim < τ 的比例（τ=0.30 主阈值 + 敏感性 0.25/0.35）
- **RR(T_k)**：漏斗层级 k 的保护效果保留率 = Δ(T_k)/Δ(T0)，Δ = 无保护−有保护的 ID-sim 差
- 攻击质量：KID、CLIP-T（可选）；公平性：LPIPS/PSNR（扰动 vs 原图）
- 统计：身份级配对 bootstrap 95% CI + Wilcoxon signed-rank + Holm 校正 + 配对 MDE（80% 功效，`runs/*/mde.csv`）

## 评测协议对齐

攻击生成协议与 Anti-DreamBooth 官方 `infer.py` 对齐：5 条标准 prompt × 多种子。
混池设置沿用其定义的 uncontrolled setting（部分无保护图混入训练集）。
