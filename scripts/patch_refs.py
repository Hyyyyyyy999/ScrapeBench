import re

path = "paper/refs.bib"
src = open(path).read()

# split into entry blocks by top-level @...{key,
entries = {}
order = []
for m in re.finditer(r"(?ms)^@(\w+)\{([^,]+),\n.*?\n\}", src):
    key = m.group(2).strip()
    entries[key] = m.group(0)
    order.append(key)

# sanity
assert "wang2024instantid" in entries and "zhu2025gapdiff" in entries, "HEAD restore incomplete"
assert len(order) == 58, f"expected 58 entries, got {len(order)}"

# 1) upgrade IDProtector to CVPR 2025
entries["song2024idprotector"] = """@inproceedings{song2024idprotector,
  title = {IDProtector: An Adversarial Noise Encoder to Protect Against ID-Preserving Image Generation},
  author = {Yiren Song and Pei Yang and Hai Ci and Mike Zheng Shou},
  year = {2025},
  booktitle = {2025 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
  pages = {3019--3028},
  publisher = {IEEE},
  doi = {10.1109/CVPR52734.2025.00287}
}"""

# 2) purge non-compliant entries (2y+ arXiv-only, or 3mo low-cite risk)
for k in ["li2024promptindependent", "zheng2023targeted", "sandovalsegura2023jpeg",
          "sandovalsegura2023what", "onikubo2024highfrequency", "guo2024improving",
          "lee2026universal"]:
    entries.pop(k, None)
    if k in order:
        order.remove(k)

# 3) new compliant entries (verified via paper_search this session)
new_entries = {
"kim2025blurguard": """@misc{kim2025blurguard,
  title = {BlurGuard: A Simple Approach for Robustifying Image Protection Against AI-Powered Editing},
  author = {Jinsu Kim and Yunhun Nam and Minseon Kim and Sangpil Kim and Jongheon Jeong},
  year = {2025},
  howpublished = {arXiv:2511.00143},
  eprint = {2511.00143},
  archivePrefix = {arXiv},
  url = {http://arxiv.org/abs/2511.00143v1}
}""",
"guo2024realtime": """@misc{guo2024realtime,
  title = {Real-time Identity Defenses against Malicious Personalization of Diffusion Models},
  author = {Hanzhong Guo and Shen Nie and Chao Du and Tianyu Pang and Hao Sun and Chongxuan Li},
  year = {2024},
  howpublished = {arXiv:2412.09844},
  eprint = {2412.09844},
  archivePrefix = {arXiv},
  url = {http://arxiv.org/abs/2412.09844v1}
}""",
"li2025antidiffusion": """@article{li2025antidiffusion,
  title = {Anti-Diffusion: Preventing Abuse of Modifications of Diffusion-Based Models},
  author = {Zheng Li and Liangbin Xie and Jiantao Zhou and Xintao Wang and Haiwei Wu and Jinyu Tian},
  year = {2025},
  journal = {Proceedings of the AAAI Conference on Artificial Intelligence},
  volume = {39},
  number = {10},
  pages = {10582--10590},
  publisher = {Association for the Advancement of Artificial Intelligence},
  doi = {10.1609/aaai.v39i10.33149}
}""",
"yang2024ddap": """@article{yang2024ddap,
  title = {DDAP: Dual-Domain Anti-Personalization against Text-to-Image Diffusion Models},
  author = {Jing Yang and Runping Xi and Yingxin Lai and Xun Lin and Zitong Yu},
  year = {2024},
  journal = {IEEE International Joint Conference on Biometrics (IJCB)},
  pages = {1--10},
  publisher = {IEEE},
  doi = {10.1109/IJCB62174.2024.10744490}
}""",
"devulapally2025latent": """@inproceedings{devulapally2025latent,
  title = {Latent Diffusion Unlearning: Protecting Against Unauthorized Personalization Through Trajectory Shifted Perturbations},
  author = {Naresh Kumar Devulapally and Shruti Agarwal and Tejas Gokhale and Vishnu Suresh Lokhande},
  year = {2025},
  booktitle = {Proceedings of the 33rd ACM International Conference on Multimedia},
  publisher = {ACM},
  doi = {10.1145/3746027.3755112}
}""",
"wang2026safeguarding": """@misc{wang2026safeguarding,
  title = {Safeguarding Facial Identity against Diffusion-based Face Swapping via Cascading Pathway Disruption},
  author = {L.F.S. Wang and Qianyue Hu and Wei Lu and Xiangyang Luo},
  year = {2026},
  howpublished = {arXiv:2601.14738},
  eprint = {2601.14738},
  archivePrefix = {arXiv},
  url = {http://arxiv.org/abs/2601.14738v1}
}""",
"zhang2026unlearnability": """@misc{zhang2026unlearnability,
  title = {SoK: Unlearnability and Unlearning for Model Dememorization},
  author = {Mengying Zhang and Derui Wang and Ruoxi Sun and Xiaoyu Xia and Shuang Hao and Minhui Xue},
  year = {2026},
  howpublished = {arXiv:2605.11592},
  eprint = {2605.11592},
  archivePrefix = {arXiv},
  url = {http://arxiv.org/abs/2605.11592v1}
}""",
"li2025detecting": """@article{li2025detecting,
  title = {Detecting and Corrupting Convolution-based Unlearnable Examples},
  author = {Minghui Li and Xianlong Wang and Zhifei Yu and Shengshan Hu and Ziqi Zhou and Longling Zhang and Leo Yu Zhang},
  year = {2025},
  journal = {Proceedings of the AAAI Conference on Artificial Intelligence},
  volume = {39},
  number = {17},
  pages = {18403--18411},
  publisher = {Association for the Advancement of Artificial Intelligence},
  doi = {10.1609/aaai.v39i17.34025}
}""",
"gong2026armor": """@article{gong2026armor,
  title = {Armor: Shielding Unlearnable Examples Against Data Augmentation},
  author = {Xueluan Gong and Yuji Wang and Yanjiao Chen and Haocheng Dong and Yiming Li and Mengyuan Sun and Shuaike Li and Qian Wang},
  year = {2026},
  journal = {IEEE Transactions on Pattern Analysis and Machine Intelligence},
  publisher = {IEEE},
  doi = {10.1109/TPAMI.2026.3652456}
}""",
"wei2025personalized": """@misc{wei2025personalized,
  title = {Personalized Image Generation with Deep Generative Models: A Decade Survey},
  author = {Yuxiang Wei and Yiheng Zheng and Yabo Zhang and Ming Liu and Zhilong Ji and Lei Zhang and Wangmeng Zuo},
  year = {2025},
  howpublished = {arXiv:2502.13081},
  eprint = {2502.13081},
  archivePrefix = {arXiv},
  url = {http://arxiv.org/abs/2502.13081v1}
}""",
"shin2026latent": """@article{shin2026latent,
  title = {Latent Diffusion Models: A Survey on Foundations, Variants, and Web-scale Deployments},
  author = {Jee-Woo Shin and Chayapol Kamyod and Chung-Pyo Hong},
  year = {2026},
  journal = {Journal of Web Engineering},
  publisher = {River Publishers},
  doi = {10.13052/jwe1540-9589.2546}
}""",
}
for k, v in new_entries.items():
    entries[k] = v
    order.append(k)

out = "\n\n".join(entries[k] for k in order) + "\n"
open(path, "w").write(out)
print("entries:", len(order))
print("purged ok; new added:", list(new_entries))
