import torch
import numpy as np
from PIL import Image


class ZeroShotFaceID:
    def __init__(self, model_id, device="cuda", adapter_repo="h94/IP-Adapter-FaceID",
                 weight_name="ip-adapter-faceid_sd15.bin", scale=0.8, face_pack="buffalo_l"):
        from diffusers import StableDiffusionPipeline
        from insightface.app import FaceAnalysis
        self.pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.bfloat16, safety_checker=None).to(device)
        self.pipe.load_ip_adapter(adapter_repo, subfolder="", weight_name=weight_name, image_encoder_folder=None)
        self.pipe.set_ip_adapter_scale(scale)
        self.pipe.set_progress_bar_config(disable=True)
        self.device = device
        self.face = FaceAnalysis(name=face_pack, providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
        self.face.prepare(ctx_id=0 if device.startswith("cuda") else -1, det_size=(640, 640))

    def _embed(self, img):
        arr = np.array(img.convert("RGB"))[:, :, ::-1]
        faces = self.face.get(arr)
        if not faces:
            return None
        f = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
        return torch.from_numpy(f.normed_embedding.astype(np.float32))[None].to(self.device, torch.float16)

    def ref_embeds(self, ref_imgs):
        pos = [e for e in (self._embed(im) for im in ref_imgs) if e is not None]
        if not pos:
            raise RuntimeError("no face detected in reference images")
        return torch.cat(pos, 0).mean(0, keepdim=True)

    @torch.no_grad()
    def generate(self, prompts, ref_imgs, n_per_prompt=1, steps=30, guidance=5.0, seed=0, height=512, width=512):
        emb = self.ref_embeds(ref_imgs)
        neg = torch.zeros_like(emb)
        out = []
        for pr in prompts:
            g = torch.Generator(device=self.device).manual_seed(seed)
            res = self.pipe(
                [pr] * n_per_prompt, num_inference_steps=steps, guidance_scale=guidance,
                generator=g, height=height, width=width,
                ip_adapter_image_embeds=[emb, neg],
            )
            out.extend(res.images)
        return out
