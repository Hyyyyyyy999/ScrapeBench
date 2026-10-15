# ScrapeBench single-intervention protocol

The revised benchmark does **not** apply a seven-step cascade. Every condition
starts from the same protected upload and applies exactly one intervention.

| Label | Independent intervention | Canonical setting | Web role |
|---|---|---|---|
| T0 | none | lossless 512 px input | direct file acquisition |
| T1 | JPEG transcode | quality 70, 4:2:0 | platform/CDN re-encoding; GAP-Diff-compatible |
| T2 | browser raster | 360 CSS px, DPR 1 | feed/card rendering |
| T3 | agent capture | face crop, WebP 80 | screenshot-and-crop crawler |
| T4 | restoration | Real-ESRGAN x2, JPEG 92 | enhancement before training |
| T5 | regeneration | SD1.5 img2img strength .30 | semantic re-rendering |
| T6 | purification | DDIM inversion/reconstruction, 50 steps | adaptive purification |

The clean and protected branches use the identical loader, center crop, resize,
intervention function, attacker, prompt, seed and scoring code. T6 is a direct
purification of the protected upload, not T5 followed by another operation.

## Primary comparison

The main benchmark uses a locally available CelebA-HQ archive with 100
identity-labelled subjects (8 gallery and 2 held-out reference images each),
split into 10 development, 80 core-test, and 10 audit identities. The
GAP-Diff-compatible block uses 30 held-out VGGFace2 identities, JPEG Q=70,
DreamBooth for 1,000 steps and 30 generations for each of its four original
prompts. The CelebA-100 main block instead uses four deployment scenarios:
social-avatar portrait, smartphone selfie, low-light indoor social photo, and
outdoor travel photo with background. It
reports FDFR, ISM, BRISQUE and SER-FIQ and creates a four-prompt qualitative
grid. Official checkpoints are required for GAP-Diff and IDProtector. AntiPure
is listed as unavailable until its authors release executable code or protected
images; it must not be represented by an in-house approximation.

## Statistical contract

For every method/tier/reader report the paired clean-minus-protected identity
gap, identity-bootstrap 95% CI, RR with a bootstrap CI, change from T0, Holm
adjusted paired tests, and a TOST equivalence test with a preregistered
`0.03` ISM smallest effect size of interest. Non-significance is never called
equivalence or collapse.
