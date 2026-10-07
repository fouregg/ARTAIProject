"""Backfill decoded pixel hashes for existing images. Safe to resume."""
import asyncio

from sqlalchemy import select
from app.db import SessionLocal, engine
from app.models import Generation
from app.services.storage import image_fingerprint, resolve_path


async def main():
    async with SessionLocal() as session:
        ids = (await session.scalars(select(Generation.id).where(
            Generation.status == "done", Generation.image_sha256.is_(None)))).all()
        missing = 0
        for index, generation_id in enumerate(ids, 1):
            row = await session.get(Generation, generation_id)
            path = resolve_path(row.file_path) if row.file_path else None
            if path is None:
                missing += 1
                continue
            row.image_sha256 = await asyncio.to_thread(lambda: image_fingerprint(path.read_bytes()))
            if index % 50 == 0:
                await session.commit()
                print(f"Fingerprinted {index}/{len(ids)}; missing files: {missing}", flush=True)
        await session.commit()
        print(f"Finished: {len(ids)} inspected, {missing} missing files", flush=True)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
