import numpy as np


class IdScorer:
    def __init__(self, pack="buffalo_l", use_gpu=True):
        from insightface.app import FaceAnalysis
        providers = ["CPUExecutionProvider"]
        self.app = FaceAnalysis(name=pack, providers=providers)
        ctx_id = -1
        self.app.prepare(ctx_id=ctx_id, det_size=(640, 640))
        self._ref_cache = {}

    def embed(self, pil_img):
        arr = np.array(pil_img.convert("RGB"))[:, :, ::-1]
        faces = self.app.get(arr)
        if not faces:
            return None, False
        f = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
        emb = f.normed_embedding.astype(np.float32)
        return emb, True

    def ref_embeddings(self, pid, ref_paths):
        if pid in self._ref_cache:
            return self._ref_cache[pid]
        from PIL import Image
        embs = []
        for p in ref_paths:
            emb, ok = self.embed(Image.open(p).convert("RGB"))
            if ok:
                embs.append(emb)
        self._ref_cache[pid] = embs
        return embs

    def best_sim(self, pil_img, ref_embs):
        emb, ok = self.embed(pil_img)
        if not ok or not ref_embs:
            return float("nan"), False
        refs = np.stack(ref_embs, 0)
        sims = refs @ emb
        return float(sims.max()), True
