# ScrapeBench experiment audit — 2026-10-17

This document separates verified facts, invalidated legacy results, pending
experiments, and paper-safe claims. It is the source of truth for the current
WWW 2027 revision.

## Executive finding

The previous experiment matrix was not ready for a strongest-method claim.
Several independent faults acted in the same direction: GoodAC failed after a
one-iteration smoke test; MetaCloak used a non-official Gaussian kernel; Stage A
used one prompt repeated four times despite being described as four scenarios;
T4 swapped RGB/BGR around Real-ESRGAN; old output PNGs survived forced reruns;
Stage B did not implement the SD2.1 DreamBooth protocol described in the paper;
and ARCP optimized FaceNet while the attacked readers use aligned ArcFace.

These are protocol/code faults, not evidence that ARCP is intrinsically weak or
strong. The corrected run must finish before any comparative ranking is made.

## Confirmed faults and disposition

| Component | Confirmed fault | Consequence | Disposition |
|---|---|---|---|
| GoodAC | Original loop retained the base model, copied surrogate, feature graphs, and optimizer cache on GPU | Every 24-GB formal task OOMed on outer iteration 2; one-step smoke falsely passed | CPU/GPU staged residency and explicit graph/cache release; three-iteration smoke `141621` passed |
| MetaCloak | Wrapper used Gaussian kernel 5; released robust configuration uses 7 | First two outputs and the running third identity were not protocol-consistent with the official configuration | Jobs `141517/141519` cancelled; outputs archived as `metacloak_invalid_k5_20261017`; corrected chain submitted |
| Prompts | Stage A configuration had one generic prompt and four samples | Existing “four-scenario” claim was false | Four distinct, fixed Web scenarios; one output per scenario |
| T4 | PIL RGB was passed to a BGR RealESRGANer and returned BGR was interpreted as RGB | Clean InstantID T4 collapsed (old FDFR 65.6%, E2E ISM .059), invalidating method ranking | Explicit RGB↔BGR conversion; Clean must be rerun |
| T6 | Implementation is prompt-free SD1.5 img2img at strength .50 | It is not official DiffPure | Paper now calls it a reconstruction/purification proxy |
| Forced reruns | JSONL was overwritten but stale PNGs remained | Numeric summaries were safe, but a qualitative panel could select an image from an older protocol | Cell directory is deleted before a forced rerun |
| DreamBooth | Old Stage B was SD1.5, UNet-only, no class-prior loss, frozen text encoder | It did not match the claimed SD2.1, prior-preserving, text-encoder-training protocol | Runner now loads SD2.1, uses 200 class images, joint instance/prior loss, and restores UNet plus text encoder per cell; two-step smoke `141633` pending |
| ARCP surrogate | FaceNet full/central-frame objective did not match detect→align→ArcFace conditioning | Large proxy improvement did not reliably transfer to InstantID/IP-Adapter | V4 adds differentiable antelopev2/glintr100 ArcFace with clean-fixed alignment and keeps FaceNet as an ensemble member |
| Pixel budget | Old ARCP-v2 PNGs reached 17/255; GAP-Diff and IDProtector reached about 9/255, MetaCloak 11/255 | Old “best” rankings were budget-confounded | V4 is capped and re-projected at 8/255; official-default and common-budget comparisons are separate |
| Statistics | Old summaries lacked RR intervals and could rank cells where Clean customization itself failed | Low identity could be caused by a broken attack rather than protection | New summary bootstraps paired identities, reports E2E/conditional ISM, FDFR, ISR, gap, RR and Δgap; non-viable Clean tiers are marked non-rankable |

## Baseline audit

### GAP-Diff

- Forty identities and 160 images are complete.
- Realized maximum pixel difference is 9 levels; mean PSNR is 31.60 dB.
- It is suitable as a released-checkpoint baseline, but final numbers must be
  regenerated under the corrected four-prompt/T4 evaluation.

### GoodAC

- Released code and published optimization counts are used: 50 outer rounds,
  3 surrogate steps, 6 adversarial steps, beta 1.625 and gamma .2.
- The paper's example guidance prompt describes one particular blonde woman.
  Web40 uses a disclosed identity-neutral guidance prompt. Therefore this is a
  released-code port, not an untouched official artifact.
- The upstream `pgd_eps=16` is applied to tensors in [-1,1], so the realized
  8-bit budget is expected near 8/255. The run records actual L-infinity and
  PSNR rather than relabeling it as 16/255.

### MetaCloak

- Corrected settings match the released robust configuration: 1,000 total
  steps, interval 200, advance 2, four trails, six defense PGD steps, radius 11,
  Gaussian kernel 7, and horizontal flip.
- The A800 account limit currently permits one task, making the 40-identity
  baseline intrinsically slow.

### IDProtector

IDProtector remains in the artifact for audit history but is excluded from the
requested main comparison. Its old results must not silently enter the new
auto-discovered table; final summarization should select exactly Clean,
GAP-Diff, MetaCloak, GoodAC, and ARCP-Web-v4.

## Seven independent interventions

Each T consumes the same T0 independently; no T is fed by the previous T.

| T | Current operation | Audit judgment |
|---|---|---|
| T0 | square 512-pixel released image | Correct control |
| T1 | resize minimum side to 512, JPEG Q70, 4:2:0 | Correct and GAP-Diff-aligned |
| T2 | render/extract a 360-CSS-pixel DPR-1 feed-card image | Reasonable Web raster proxy; not a real browser trace |
| T3 | face detector crop, .35 margin, resize 512, WebP 80 | Reasonable agent screenshot proxy; Haar-first crop should be reported |
| T4 | Real-ESRGAN x2 then JPEG 92 | Implementation repaired; old results invalid |
| T5 | SD1.5 img2img, strength .30, 30 steps | Generative re-upload proxy |
| T6 | prompt-free SD1.5 img2img, strength .50, 50 steps | Purification proxy, not DiffPure |

A T is rankable only if the Clean attack detects at least 50% of generated
faces and retains at least 50% of its T0 end-to-end ISM. Invalid T values remain
visible but cannot support “method X is strongest.”

## Customization audit

- **InstantID:** native best-detection gallery reference, SDXL, 30 steps,
  guidance 5. It uses antelopev2 conditioning.
- **IP-Adapter-FaceID:** normalized mean of all detectable gallery embeddings,
  SD1.5, 30 steps, guidance 5. A fixed negative prompt is now used to reduce
  malformed clean outputs.
- **DreamBooth:** corrected SD2.1 full-UNet plus text-encoder training, 1,000
  steps, class-prior weight 1, and 200 class-person images. It is not part of a
  full grid until the memory smoke passes.
- Four generation scenarios are front-facing social avatar, smartphone selfie,
  low-light indoor social image, and outdoor travel image. Prompts, seeds and
  sample counts are identical within every clean/protected pair.

## ARCP-Web-v4 design and falsification gate

V4 is independent: it starts from clean images and never reads GAP-Diff,
MetaCloak, GoodAC, or IDProtector outputs. It uses a realized 8/255 limit,
128-grid plus full-resolution detail parameterization, balanced T0–T6 proxy
updates, dual T0 loss, SD1.5 denoising loss, FaceNet, and a differentiable copy
of InstantID's released ArcFace recognizer. The ArcFace conversion and backward
gradient were tested locally (512-dimensional output, finite input gradient).

This change addresses a measured model mismatch; it does not guarantee a win.
The four-identity gate `141627 → 141628` determines whether V4 proceeds. A full
40-identity run is justified only if it improves the preregistered aggregate
without violating quality or budget checks.

## Current paper-safe conclusions

1. The 40-identity cohort itself is real and audited: four gallery and two
   held-out references per identity. This is not evidence of defense efficacy.
2. Old results show that T0–T3 are viable for both zero-shot readers, while old
   Clean T4–T6 failed the viability criterion for at least one reader. Because
   T4 contained a color bug and the prompt protocol was wrong, these are
   diagnostics only.
3. Old GAP-Diff T0–T3 gaps were small and their paired intervals crossed zero;
   that does not prove ineffectiveness, only insufficient evidence in that run.
4. Old ARCP-v2 produced large positive T0–T3 gaps, but used one prompt and an
   effective 17/255 maximum. It cannot support a matched-budget superiority
   claim.
5. No corrected result currently proves ARCP-Web-v4 strongest. Any statement
   to the contrary would be fabricated.

## Submitted corrected jobs (snapshot)

| Purpose | Jobs | Dependency / throttle |
|---|---|---|
| GoodAC smoke → 40-ID protection → zero-shot evaluation | `141621 → 141622 → 141625` | smoke passed; protection throttle reduced to 4 |
| Four-scenario Clean gate/full evaluation | `141623 → 141624` | full throttle 1, paired dependency for GoodAC evaluation |
| MetaCloak smoke → 40-ID protection → evaluation | `141629 → 141630 → 141631` | smoke passed; A800 full throttle 1 |
| ARCP-Web-v4 four-ID protection/evaluation | `141627 → 141628` | protection throttle 1 |
| Corrected DreamBooth memory smoke | `141633` | scheduled after current GoodAC evaluation |

The active 4090 policy is GoodAC 4 + Clean 1 + ARCP-v4 1, never more than six
concurrent 4090 tasks. MetaCloak uses one A800 separately.

## Timing based on measured jobs

- Historical Stage-A shards took approximately 38–65 minutes each. At Clean's
  conservative throttle 1, its 20 shards require roughly 13–22 GPU-hours after
  the gate, excluding queue delay.
- Corrected MetaCloak previously required about 71 minutes per identity on an
  A800. With the account's one-A800 QOS limit, 40 identities require roughly 47
  compute-hours plus queue delay.
- GoodAC's three-round smoke took 3 minutes 42 seconds. A 50-round identity is
  expected to take substantially longer; a defensible completion estimate must
  wait for the first corrected full identity rather than extrapolating linearly
  from the cheaper smoke.
- ARCP-v3 four-identity generation took about 24 minutes. V4 has more updates
  and an added ArcFace branch, so its four-ID gate is expected to take several
  hours at throttle 1, subject to queue availability.

## Files changed by this audit

- `GoodAC/attacks/goodac.py`
- `scrapebench/protection/arcp.py`
- `scrapebench/funnel/restore.py`
- `scrapebench/attack/ip_adapter.py`
- `scrapebench/attack/train_utils.py`
- `scrapebench/runner/stage_a.py`
- `scrapebench/runner/stage_b.py`
- `configs/web40_single_intervention.yaml`
- `scripts/run_official_web40_protector.py`
- `scripts/summarize_web40.py`
- corrected Slurm entry points under `slurm/`
