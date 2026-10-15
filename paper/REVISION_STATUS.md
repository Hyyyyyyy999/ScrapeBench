# WWW 2027 review assessment and revision status

## Assessment

The review's central objections are reasonable and publication-critical.

1. The clean/protected preprocessing mismatch invalidates a causal reading of
   the original main table. The corrected experiment must regenerate both
   branches through the same loader and cannot combine old and corrected rows.
2. Failure to reject a null is not evidence that a protection “collapses.” The
   revision therefore reports paired absolute gaps and identity-bootstrap CIs,
   RR with CIs, change from T0, and TOST equivalence at a preregistered 0.03 ISM
   bound. The title and claims no longer presume collapse.
3. Omitting GAP-Diff and IDProtector makes a 2027 comparison incomplete. Both
   are run from official checkpoints at their released settings; measured
   pixel budgets are reported explicitly instead of calling different internal
   scalings a matched budget.
   AntiPure has no verified public executable artifact in the repository audit;
   it will be marked unavailable rather than approximated and mislabeled.
4. Simulated web operations alone do not establish platform fidelity. JPEG Q70
   provides a published anchor; a separate paired upload/download validation is
   still required for claims about named services.
5. Six-identity ARCP evidence is exploratory. The revised fixed split uses 10
   development identities, 80 core test identities and 10 untouched audit
   identities. Hyperparameters are frozen before the 90 test identities run.
6. A URL manifest is policy metadata, not a pixel-persistent protection. The
   revision limits its claim accordingly and does not count it as T0--T6 defense.

## Experiment committed in code

- CelebA-HQ-100: 8 gallery images and 2 held-out references per identity,
  prepared entirely from the server's local 3.9-GB archive and public identity
  metadata so compute jobs do not depend on outbound network access.
- Seven independent conditions: T0 raw; T1 JPEG Q70; T2 browser raster; T3
  agent face crop; T4 Real-ESRGAN; T5 img2img; T6 diffusion purification.
- Equal processing for clean and protected branches.
- DreamBooth main block: 1,000 steps, four Web scenarios (avatar, selfie,
  low-light social, outdoor travel), 30 outputs per identity/scenario,
  FDFR/ISM/BRISQUE/SER-FIQ, plus a Figure-8-style grid. A separate VGGFace2
  Q70 block retains GAP-Diff's exact prompts for direct table comparability.
- Readers: DreamBooth-LoRA, IP-Adapter-FaceID and InstantID.
- Defenses: official GAP-Diff and IDProtector artifacts, ARCP-v2, clean control;
  older FSMG/ASPL results are secondary rather than the headline comparison.
- ARCP-v2 uses a true 16/255 pixel-space cap. Legacy ARCP used 16/255 on a
  [-1,1] tensor (an effective 8/255 pixel cap) and remains labeled legacy.

Numerical tables in the manuscript must only be replaced after the new jobs
finish. The code intentionally does not insert anticipated superiority claims.

## Live execution snapshot (2026-10-15, Asia/Shanghai)

- GAP-Diff protection: 90/90 evaluation identities, 720/720 images complete.
- ARCP-v2 protection: 7/90 identities complete at the 19:13 snapshot. Their
  mean PSNR is 34.21 dB (range 34.05--34.47 dB); this partial quality audit is not a
  defense-performance estimate.
- IDProtector protection: 0/90 complete. The first submission selected an
  environment without PyTorch; the corrected submission uses the previously
  validated UMO environment and the official 0.07 setting (about 9/255).
- Stage A and Stage B: waiting for their protected-gallery dependencies; no
  revised FDFR/ISM/BRISQUE/SER-FIQ result exists yet.
- Scheduler constraint: the account QOS currently permits one GPU at a time.
  Protection and Stage A use an RTX 4090; full-UNet Stage B uses an RTX Pro
  6000. Idle GPUs elsewhere in the cluster do not raise this per-user limit.
