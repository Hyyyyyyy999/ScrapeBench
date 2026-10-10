# Attribution

ScrapeBench reimplements and extends published protective-perturbation defenses.
We gratefully acknowledge the following works:

- **Anti-DreamBooth** (Thanh Van Le et al., ICCV 2023, VinAI Research).
  AGPL-3.0. Official code: https://github.com/VinAIResearch/Anti-DreamBooth
  Our `scrapebench/protection/fsmg.py` and `aspl_lite.py` are independent
  re-implementations of the FSMG / ASPL formulations (surrogate-guided PGD on
  the DreamBooth conditional objective). The evaluation protocol (5 standard
  prompts, uncontrolled mixed-pool setting) follows the official repository.
- **MetaCloak** (Yixin Liu et al., CVPR 2024 Oral).
  Official code: https://github.com/liuyixin-louis/MetaCloak
  Its `gen_and_eval.sh` / `methods_config.sh` harness inspired our runner design.
- **SimAC** (Feifei Wang et al., CVPR 2024).
  Official code: https://github.com/somuchtome/SimAC
- **PhotoGuard** (Salman et al., ICML 2023).
  Official code: https://github.com/MadryLab/photoguard
- **JPEG bypass finding** (Sandoval-Segura et al., 2023, arXiv:2304.02234)
  motivated the JPEG-quality sweep at funnel tier T1.
- **IP-Adapter-FaceID** (h94). The optional vendored adapter file under
  `vendor/` originates from https://github.com/h94/IP-Adapter-FaceID (Apache-2.0
  / original license headers preserved in-file).
- **Comprehensive evaluation prior** (Kai Ye et al., arXiv:2507.03953):
  ScrapeBench differs by evaluating under the realistic Web acquisition funnel
  (browser/agent capture, restoration, diffusion regeneration, adaptive mixing),
  adding zero-shot attackers and a deployment-cost axis.

All third-party components remain under their original licenses.
