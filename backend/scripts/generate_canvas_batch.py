"""Run with: python -m scripts.generate_canvas_batch --root /batch --concurrency 4.

Manifest and status live in --root. Successful generations are pinned immediately;
resume skips them. An unresolved in-flight generation requires manual inspection.
Publication happens in manifest order only after all 500 images have succeeded.
"""
import argparse
import asyncio
from collections import Counter
from datetime import datetime, timezone
import json
import logging
from pathlib import Path

import httpx
from sqlalchemy import func, select, text, update

from app.config import get_settings
from app.db import SessionLocal, engine
from app.models import DomeItem, GalleryItem, Generation, User
from app.schemas import GenerateRequest
from app.services.generation import run_generation_job
from app.services.jobs import registry
from app.services.provod import ProvodClient
from app.services.storage import image_fingerprint, resolve_path

FATAL = {"INSUFFICIENT_BALANCE", "FIRST_TOP_UP_REQUIRED", "UNAUTHORIZED", "INTERNAL_ERROR",
         "MODEL_PARAMETER_COMBINATION_INVALID"}


async def run(root: Path, concurrency: int) -> int:
    plan = json.loads((root / "manifest.json").read_text())
    prompts = plan["prompts"]
    assert plan["target"] == len(prompts) == len(set(prompts)) == 500
    assert all(0 < len(prompt) <= 2000 for prompt in prompts)
    settings = get_settings()
    completed = {}
    errors = []
    stopped = asyncio.Event()
    capacity_failures = 0
    retry_after = 0.0

    def report(state):
        data = {"batch": plan["batch"], "state": state, "target": len(prompts),
                "completed": len(completed), "remaining": len(prompts) - len(completed),
                "updated_at": datetime.now(timezone.utc).isoformat(), "errors": errors}
        tmp = root / "status.tmp"
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        tmp.replace(root / "status.json")

    async with engine.connect() as lock:
        if not await lock.scalar(text("SELECT pg_try_advisory_lock(20261007, 500)")):
            raise RuntimeError("Another batch process is running")
        async with SessionLocal() as session:
            user = await session.scalar(select(User).where(User.display_name == plan["batch"]))
            if user is None:
                user = User(display_name=plan["batch"], is_active=False, generations_limit=0)
                session.add(user)
                await session.commit()
            user_id = user.id
            previous = (await session.scalars(select(Generation).where(Generation.user_id == user_id))).all()
            assert not any(row.status in ("pending", "running") for row in previous), "Inspect unresolved requests before resuming"
            attempts = Counter(row.prompt_original for row in previous
                               if row.error != "Сервис генерации сейчас не отвечает. Попробуйте ещё раз через минуту.")
            fingerprints = set()
            for row in previous:
                if row.status != "done":
                    continue
                assert row.prompt_original in prompts and row.prompt_original not in completed
                path = resolve_path(row.file_path)
                assert path is not None, f"Missing image {row.id}"
                fingerprint = image_fingerprint(path.read_bytes())
                assert fingerprint not in fingerprints, "Duplicate batch pixels; inspect before resuming"
                fingerprints.add(fingerprint)
                completed[row.prompt_original] = row.id
            await session.execute(update(GalleryItem).where(GalleryItem.user_id == user_id).values(is_auto=False))
            await session.commit()

        queue = asyncio.Queue()
        for prompt in prompts:
            if prompt not in completed:
                queue.put_nowait(prompt)

        async def worker(client):
            nonlocal capacity_failures, retry_after
            while not stopped.is_set() and not queue.empty():
                if (root / "STOP").exists():
                    errors.append("Operator stop requested")
                    stopped.set()
                    break
                delay = retry_after - asyncio.get_running_loop().time()
                if delay > 0:
                    await asyncio.sleep(min(delay, 60))
                    continue
                prompt = queue.get_nowait()
                if attempts[prompt] >= 3:
                    errors.append("Attempt limit reached: " + prompt)
                    stopped.set()
                    break
                attempts[prompt] += 1
                job = registry.create()
                await run_generation_job(job, GenerateRequest(prompt=prompt, lang="en", skip_translation=True,
                                                             quality=plan["quality"]), client, user_id)
                if job.status == "done":
                    capacity_failures = 0
                    async with SessionLocal() as session:
                        row = await session.get(Generation, job.generation.id)
                        path = resolve_path(row.file_path)
                        assert path is not None, f"Missing image {row.id}"
                        fingerprint = image_fingerprint(path.read_bytes())
                        # Workers share one event loop: check and insert have no await between them.
                        duplicate = fingerprint in fingerprints
                        if not duplicate:
                            fingerprints.add(fingerprint)
                        row.image_sha256 = fingerprint
                        if duplicate:
                            row.status = "error"
                            row.error = "Duplicate batch pixels"
                        else:
                            await session.execute(update(GalleryItem).where(
                                GalleryItem.generation_id == row.id).values(is_auto=False))
                        await session.commit()
                        if not duplicate:
                            completed[prompt] = row.id
                    if duplicate:
                        queue.put_nowait(prompt)
                else:
                    errors.append(f"{job.error_code}: {job.error}")
                    if job.error_code == "IMAGE_CAPACITY_BUSY":
                        attempts[prompt] -= 1
                        capacity_failures += 1
                        retry_after = asyncio.get_running_loop().time() + 60
                        queue.put_nowait(prompt)
                        if capacity_failures >= 30:
                            stopped.set()
                    elif job.error_code in FATAL or sum(not error.startswith("IMAGE_CAPACITY_BUSY:") for error in errors) >= 10:
                        stopped.set()
                    else:
                        queue.put_nowait(prompt)
                report("running")
                logging.info("BATCH_PROGRESS %s/500", len(completed))

        report("running")
        async with httpx.AsyncClient(base_url=settings.provod_base_url, headers={
            "Authorization": f"Bearer {settings.provod_api_key}", "Content-Type": "application/json"
        }) as http:
            results = await asyncio.gather(*(worker(ProvodClient(http)) for _ in range(concurrency)), return_exceptions=True)
        for result in results:
            if isinstance(result, BaseException):
                errors.append(f"{type(result).__name__}: {result}")
        if len(completed) != len(prompts):
            report("stopped")
            return 1

        async with SessionLocal() as session:
            position = await session.scalar(select(func.max(DomeItem.position))) or 0
            for prompt in prompts:
                generation_id = completed[prompt]
                await session.scalar(select(Generation).where(Generation.id == generation_id).with_for_update())
                existing = await session.scalar(select(DomeItem).where(
                    DomeItem.generation_id == generation_id, DomeItem.is_visible.is_(True)))
                if existing is None:
                    position += 1
                    session.add(DomeItem(generation_id=generation_id, position=position, is_visible=True))
            await session.commit()
        report("complete")
        return 0


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--concurrency", type=int, default=4, choices=range(1, 17))
    args = parser.parse_args()
    try:
        return await run(args.root, args.concurrency)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(asyncio.run(main()))
