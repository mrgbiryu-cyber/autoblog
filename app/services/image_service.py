import asyncio
import base64
import json
import logging
import os

import httpx
from fastapi import BackgroundTasks

LOGGER = logging.getLogger("image_service")

COMFYUI_API_URL = os.getenv("COMFYUI_API_URL", "http://127.0.0.1:8188")
WORKFLOW_PATH = os.getenv("COMFYUI_WORKFLOW_PATH", "workflows/ai_marketing.json")


def load_workflow(workflow_path: str) -> dict:
    """JSON 워크플로우를 로드해서 필요한 prompt 설정을 업데이트합니다."""
    with open(workflow_path, encoding="utf-8") as fp:
        workflow = json.load(fp)
    return workflow


async def _run_comfy_workflow(workflow_path: str, prompt: str) -> bytes:
    """ComfyUI로 workflow를 보내고 base64 이미지를 받아옵니다."""
    workflow = load_workflow(workflow_path)
    payload = {
        "workflow": workflow,
        "inputs": {"prompt": prompt},
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(f"{COMFYUI_API_URL}/api/v1/workflow/run", json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            LOGGER.error("ComfyUI request failed (%s)", exc)
            raise
        data = resp.json()

    images = data.get("images") or []
    if not images:
        raise RuntimeError("ComfyUI returned no images")

    image_b64 = images[0].get("image") or images[0].get("image_base64")
    if not image_b64:
        raise RuntimeError("ComfyUI payload missing `image` key")

    return base64.b64decode(image_b64)


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
            os.makedirs("generated_images", exist_ok=True)
            with open(os.path.join("generated_images", file_name), "wb") as fp:
                fp.write(result_bytes)
            LOGGER.info("이미지 생성 완료: %s", file_name)
        except Exception as exc:
            LOGGER.error("배경 이미지 생성 중 오류: %s", exc)

    background_tasks.add_task(_task)
    return "이미지 생성 작업이 백그라운드에서 시작되었습니다."


async def generate_image_sync(workflow_path: str, prompt: str) -> bytes:
    """
    즉시 결과를 받고 싶은 경우 호출할 수 있는 동기 함수.
    """
    try:
        return await _run_comfy_workflow(workflow_path, prompt)
    except httpx.HTTPError as exc:
        LOGGER.warning("ComfyUI 서버 연결 실패: %s", exc)
        raise

