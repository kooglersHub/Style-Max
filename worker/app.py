import hmac
import io
import logging
import os
from threading import Lock

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image

from stylemax.media import normalize_image

log = logging.getLogger(__name__)


def create_worker(pipeline=None):
    app = FastAPI(title="Style-Max image worker")
    lock = Lock()
    state = {"pipeline": pipeline}

    def load_pipeline():
        if state["pipeline"] is None:
            import torch
            from diffusers import QwenImageEditPlusPipeline

            if not torch.cuda.is_available():
                raise RuntimeError("A supported CUDA GPU is required for this worker")
            model = os.getenv("STYLEMAX_IMAGE_MODEL", "Qwen/Qwen-Image-Edit-2509")
            value = QwenImageEditPlusPipeline.from_pretrained(model, torch_dtype=torch.bfloat16)
            value.enable_model_cpu_offload()
            state["pipeline"] = value
        return state["pipeline"]

    @app.get("/health")
    def health():
        return {"status": "ok", "loaded": state["pipeline"] is not None}

    @app.post("/generate")
    def generate(
        prompt: str = Form(..., min_length=10, max_length=5000),
        images: list[UploadFile] = File(...),
        authorization: str | None = Header(None),
    ):
        key = os.getenv("STYLEMAX_IMAGE_WORKER_KEY", "")
        if key and not hmac.compare_digest(authorization or "", "Bearer " + key):
            raise HTTPException(401, "Invalid worker key")
        if not 1 <= len(images) <= 3:
            raise HTTPException(422, "Provide 1-3 reference images")
        references = [
            Image.open(io.BytesIO(normalize_image(image.file.read(10 * 1024 * 1024 + 1))))
            for image in images
        ]
        if not lock.acquire(blocking=False):
            raise HTTPException(429, "Worker is busy; retry after the current image completes")
        try:
            result = load_pipeline()(
                image=references,
                prompt=prompt,
                negative_prompt=" ",
                true_cfg_scale=4.0,
                num_inference_steps=30,
                guidance_scale=1.0,
                num_images_per_prompt=1,
                width=768,
                height=1024,
            ).images[0]
            output = io.BytesIO()
            result.save(output, "PNG")
            return Response(output.getvalue(), media_type="image/png")
        except Exception as error:
            log.warning("Image worker inference failed: %s", type(error).__name__)
            raise HTTPException(
                503, "Image inference failed; check GPU, model weights and worker logs"
            ) from None
        finally:
            lock.release()
            for image in references:
                image.close()

    return app


app = create_worker()
