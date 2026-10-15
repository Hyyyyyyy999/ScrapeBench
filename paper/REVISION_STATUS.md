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
   will be run from official checkpoints at a matched 16/255 pixel budget.
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

- CelebA-100: 8 gallery images and 2 held-out references per identity.
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
