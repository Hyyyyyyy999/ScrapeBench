import os
import sys
import cv2
import numpy as np
import torch
from PIL import Image

REPO = os.environ.get("INSTANTID_REPO", os.path.expanduser("~/instantid_repo"))
FACE_ROOT = os.environ.get("INSIGHTFACE_ROOT", os.path.expanduser("~/.insightface"))


class ZeroShotInstantID:
    def __init__(self, model_id="stabilityai/stable-diffusion-xl-base-1.0", device="cuda",
                 adapter_repo="InstantX/InstantID", controlnet_repo="InstantX/InstantID",
                 scale=0.8, face_pack="antelopev2"):
        from insightface.app import FaceAnalysis
        if REPO not in sys.path:
            sys.path.insert(0, REPO)
        from diffusers import ControlNetModel
        from pipeline_stable_diffusion_xl_instantid import StableDiffusionXLInstantIDPipeline
        controlnet = ControlNetModel.from_pretrained(controlnet_repo, subfolder="ControlNetModel", torch_dtype=torch.float16)
        self.pipe = StableDiffusionXLInstantIDPipeline.from_pretrained(
            model_id, controlnet=controlnet, torch_dtype=torch.float16, variant="fp16",
            safety_checker=None).to(device)
        from huggingface_hub import hf_hub_download
        ckpt = hf_hub_download(adapter_repo, "ip-adapter.bin")
        self.pipe.load_ip_adapter_instantid(ckpt, scale=scale)
        self.pipe.set_progress_bar_config(disable=True)
        self.device = device
        self.dtype = self.pipe.dtype
        self.face = FaceAnalysis(name=face_pack, root=FACE_ROOT,
                                 providers=["CPUExecutionProvider"])
        self.face.prepare(ctx_id=-1, det_size=(640, 640))

    def _largest(self, img):
        arr = np.array(img.convert("RGB"))[:, :, ::-1]
        faces = self.face.get(arr)
        if not faces:
            return None
        return max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))

    def ref_cond(self, ref_imgs):
        embs, crops = [], []
        for im in ref_imgs:
            f = self._largest(im)
            if f is None:
                continue
            arr = np.array(im.convert("RGB"))[:, :, ::-1]
            embs.append(f.embedding.astype(np.float32))
            crops.append(arr)
        if not embs:
            raise RuntimeError("no face detected in reference images")
        return np.mean(embs, axis=0), crops[0]

    @torch.no_grad()
    def generate(self, prompts, ref_imgs, n_per_prompt=1, steps=25, guidance=5.0, seed=0,
                 height=1024, width=1024, controlnet_scale=0.8):
        emb, ref_arr = self.ref_cond(ref_imgs)
        face_emb = torch.from_numpy(emb)[None].to(self.device, self.dtype)
        f = self.face.get(ref_arr)
        face_img = Image.fromarray(cv2.resize(ref_arr[:, :, ::-1], (width, height)))
        if f:
            from pipeline_stable_diffusion_xl_instantid import draw_kps
            face_img = draw_kps(Image.fromarray(ref_arr[:, :, ::-1]), f[0].kps)
        pair = torch.cat([torch.zeros_like(face_emb), face_emb], dim=0).unsqueeze(1)
        out = []
        for pr in prompts:
            g = torch.Generator(device=self.device).manual_seed(seed)
            res = self.pipe([pr] * n_per_prompt, num_inference_steps=steps,
                            guidance_scale=guidance, generator=g,
                            height=height, width=width,
                            ip_adapter_image_embeds=[pair], ip_adapter_image=face_img,
                            controlnet_conditioning_scale=controlnet_scale)
            out.extend(res.images)
        return out
