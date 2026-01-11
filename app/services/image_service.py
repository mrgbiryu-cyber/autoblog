import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import BackgroundTasks

LOGGER = logging.getLogger("image_service")

COMFYUI_API_URL = os.getenv("COMFYUI_API_URL", "http://127.0.0.1:8188")
COMFYUI_TIMEOUT_SECONDS = float(os.getenv("COMFYUI_TIMEOUT_SECONDS", "120"))


def resolve_workflow_path() -> str:
    """
    AS-IS: 상대경로(workflows/ai_marketing.json)에 의존해서 실행 위치가 바뀌면 FileNotFound가 발생.
    TO-BE: 프로젝트 루트 기준으로 안전하게 절대경로를 만들고,
          사용자 요구사항에 따라 `~/autoblog/backend/workflows/ai_marketing.json`도 우선 후보로 둡니다.
    """
    env_path = os.getenv("COMFYUI_WORKFLOW_PATH")
    if env_path:
        return env_path

    project_root = Path(__file__).resolve().parents[2]  # .../autoblog
    candidates = [
        project_root / "backend" / "workflows" / "ai_marketing.json",
        project_root / "workflows" / "ai_marketing.json",
    ]
    for p in candidates:
        if p.exists():
            return str(p)

    # 기본 위치(루트/workflows)에 생성
    target = candidates[-1]
    target.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.warning("Workflow file missing. Creating default workflow at %s", target)
    # repo에 포함된 기본 워크플로우를 사용(없으면 최소 템플릿 생성)
    default = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"}},
        "2": {"class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 512, "batch_size": 1}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": "AI marketing automation"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": "blurry, low quality"}},
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["2", 0],
                "seed": 123456789,
                "steps": 25,
                "cfg": 7,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1,
            },
        },
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"filename_prefix": "ai_marketing", "images": ["6", 0]}},
    }
    target.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(target)


WORKFLOW_PATH = resolve_workflow_path()

# GCP 서버에 저장되는 이미지 폴더(정적 서빙 대상)
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # .../autoblog
GENERATED_DIR = PROJECT_ROOT / "static" / "generated_images"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def save_image_bytes(filename: str, image_bytes: bytes) -> str:
    """
    AS-IS: 로컬 디스크(generated_images)에 저장 → GCP에서 다운로드 불가
    TO-BE: GCP 서버의 static/generated_images 에 저장하고,
          /generated_images/<filename> URL로 접근 가능하게 합니다.
    """
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    target = GENERATED_DIR / filename
    target.write_bytes(image_bytes)
    return f"/generated_images/{filename}"


def load_workflow(workflow_path: str) -> dict:
    """JSON 워크플로우를 로드해서 필요한 prompt 설정을 업데이트합니다."""
    with open(workflow_path, encoding="utf-8") as fp:
        workflow = json.load(fp)
    return workflow


def _inject_prompt(workflow: dict, prompt: str) -> dict:
    """
    기본 워크플로우의 positive CLIPTextEncode 노드("3")에 prompt를 주입합니다.
    """
    wf = json.loads(json.dumps(workflow))  # deep copy
    node = wf.get("3")
    if isinstance(node, dict):
        inputs = node.get("inputs") or {}
        if isinstance(inputs, dict):
            inputs["text"] = prompt
            node["inputs"] = inputs
            wf["3"] = node
    return wf


async def _wait_for_image(client: httpx.AsyncClient, prompt_id: str, timeout_s: float = 120.0) -> dict:
    start = asyncio.get_event_loop().time()
    while True:
        if asyncio.get_event_loop().time() - start > timeout_s:
            raise TimeoutError("ComfyUI history polling timed out")

        resp = await client.get(f"{COMFYUI_API_URL}/history/{prompt_id}")
        resp.raise_for_status()
        history = resp.json() or {}
        item = history.get(prompt_id) or {}
        outputs = item.get("outputs") or {}
        # outputs: {node_id: {"images":[{"filename":...,"subfolder":...,"type":"output"}] } }
        for _, out in outputs.items():
            images = out.get("images") if isinstance(out, dict) else None
            if images and isinstance(images, list) and images:
                img0 = images[0]
                if isinstance(img0, dict) and img0.get("filename"):
                    return img0

        await asyncio.sleep(0.5)


async def _run_comfy_workflow(workflow_path: str, prompt: str) -> bytes:
    """
    표준 ComfyUI API 기반 실행:
    - POST /prompt  { "prompt": <workflow> }
    - GET  /history/{prompt_id}
    - GET  /view?filename=...&subfolder=...&type=...
    """
    workflow = load_workflow(workflow_path)
    workflow = _inject_prompt(workflow, prompt)

    timeout = httpx.Timeout(COMFYUI_TIMEOUT_SECONDS, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            submit = await client.post(f"{COMFYUI_API_URL}/prompt", json={"prompt": workflow})
            submit.raise_for_status()
            payload = submit.json() or {}
            prompt_id = str(payload.get("prompt_id") or "")
            if not prompt_id:
                raise RuntimeError(f"ComfyUI returned no prompt_id: {payload}")

            img_meta = await _wait_for_image(client, prompt_id)
            filename = img_meta.get("filename")
            subfolder = img_meta.get("subfolder", "")
            img_type = img_meta.get("type", "output")

            view = await client.get(
                f"{COMFYUI_API_URL}/view",
                params={"filename": filename, "subfolder": subfolder, "type": img_type},
            )
            view.raise_for_status()
            return view.content
        except httpx.ConnectError as exc:
            LOGGER.error("ComfyUI connection error (%s): %s", COMFYUI_API_URL, exc)
            raise
        except httpx.TimeoutException as exc:
            LOGGER.error("ComfyUI timeout (%s): %s", COMFYUI_API_URL, exc)
            raise
        except httpx.HTTPStatusError as exc:
            LOGGER.error("ComfyUI HTTP error (%s): %s", COMFYUI_API_URL, exc)
            raise
        except FileNotFoundError as exc:
            LOGGER.error("Workflow file not found (%s): %s", workflow_path, exc)
            raise
        except Exception as exc:
            LOGGER.error("ComfyUI workflow run failed (%s): %s", type(exc).__name__, exc)
            raise


async def generate_image_background(
    workflow_path: str, prompt: str, background_tasks: BackgroundTasks
) -> str:
    """
    BackgroundTasks에 이미지 생성 작업을 등록하고 API 호출 상태를 문자열로 반환합니다.
    """

    async def _task():
        try:
            result_bytes = await _run_comfy_workflow(workflow_path, prompt)
            file_name = f"comfy_{int(asyncio.get_event_loop().time())}.png"
            url = save_image_bytes(file_name, result_bytes)
            LOGGER.info("이미지 생성 완료: %s", url)
        except Exception as exc:
            LOGGER.exception("배경 이미지 생성 중 오류(%s): %s", type(exc).__name__, exc)

    background_tasks.add_task(_task)
    return "이미지 생성 작업이 백그라운드에서 시작되었습니다."


async def generate_image_sync(workflow_path: str, prompt: str) -> bytes:
    """
    즉시 결과를 받고 싶은 경우 호출할 수 있는 동기 함수.
    """
    return await _run_comfy_workflow(workflow_path, prompt)

