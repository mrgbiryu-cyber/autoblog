"""
ComfyUI 작업을 FIFO 대기열로 순차 처리하여 로컬 부하를 보호하는 큐 모듈.
[cite: 2025-12-23]
"""

import asyncio
import os

from app.services.image_service import generate_image_sync
from app.services.image_service import WORKFLOW_PATH
import logging

LOGGER = logging.getLogger("generation_queue")

# 이미지 생성 대기열 (FIFO)
image_queue: asyncio.Queue[tuple[int, int, str]] = asyncio.Queue()


async def update_db_status(post_id: int, img_index: int, status: str) -> None:
    LOGGER.info("Post %s image %s status -> %s", post_id, img_index, status)
    # TODO: 실제 DB 갱신 로직 필요


async def save_image_and_complete(post_id: int, img_index: int, image_bytes: bytes) -> None:
    os.makedirs("generated_images", exist_ok=True)
    file_path = os.path.join("generated_images", f"post_{post_id}_image_{img_index}.png")
    with open(file_path, "wb") as fp:
        fp.write(image_bytes)
    LOGGER.info("Image saved (%s)", file_path)
    await update_db_status(post_id, img_index, "completed")


async def worker() -> None:
    """로컬 ComfyUI를 위해 하나씩 처리하는 일꾼"""
    while True:
        post_id, img_index, prompt = await image_queue.get()
        try:
            await update_db_status(post_id, img_index, "processing")
            result = await generate_image_sync(WORKFLOW_PATH, prompt)
            await save_image_and_complete(post_id, img_index, result)
        except Exception as exc:
            LOGGER.error("Image generation task failed: %s", exc)
            await update_db_status(post_id, img_index, "failed")
        finally:
            image_queue.task_done()


def start_worker(loop: asyncio.AbstractEventLoop | None = None) -> None:
    loop = loop or asyncio.get_event_loop()
    loop.create_task(worker())

