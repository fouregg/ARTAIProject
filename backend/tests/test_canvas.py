import asyncio
import io
import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from PIL import Image, PngImagePlugin
from sqlalchemy import func, select, text

from app.api.routes.dome import _load_items, display_on_dome, dome_preview
from app.db import SessionLocal, engine
from app.models import DomeItem, Generation, User
from app.schemas import DomeDisplayRequest
from app.services.storage import image_fingerprint
from scripts.build_canvas_prompts import SUBJECTS, manifest


class PromptTests(unittest.TestCase):
    def test_manifest_variety_on_each_page(self):
        prompts = manifest()["prompts"]
        self.assertEqual(len(set(prompts)), 500)
        for offset in range(0, 500, 50):
            subjects = [next(subject for subject in SUBJECTS if subject in prompt)
                        for prompt in prompts[offset:offset + 50]]
            self.assertEqual(len(set(subjects)), 50)

    def test_pixel_hash_ignores_encoding_metadata(self):
        source = Image.new("RGB", (16, 16), "red")
        plain, annotated = io.BytesIO(), io.BytesIO()
        source.save(plain, "PNG")
        meta = PngImagePlugin.PngInfo()
        meta.add_text("comment", "different file, identical picture")
        source.save(annotated, "PNG", pnginfo=meta)
        self.assertNotEqual(plain.getvalue(), annotated.getvalue())
        self.assertEqual(image_fingerprint(plain.getvalue()), image_fingerprint(annotated.getvalue()))
        other = io.BytesIO()
        Image.new("RGB", (16, 16), "blue").save(other, "PNG")
        self.assertNotEqual(image_fingerprint(plain.getvalue()), image_fingerprint(other.getvalue()))


class CanvasDatabaseTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Run only against a disposable database explicitly named *_test.
        self.assertTrue(engine.url.database.endswith("_test"))
        async with engine.begin() as connection:
            await connection.execute(text("TRUNCATE users CASCADE"))
        async with SessionLocal() as session:
            user = User(display_name="canvas-test", is_active=False)
            session.add(user)
            await session.flush()
            self.user_id = user.id
            await session.commit()

    async def asyncTearDown(self):
        await engine.dispose()

    async def add_generation(self, prompt="unique prompt", fingerprint=None):
        async with SessionLocal() as session:
            generation = Generation(id=uuid.uuid4(), user_id=self.user_id, prompt_original=prompt,
                                    model="test", size="1024x1024", quality="low", status="done",
                                    file_path="test.png", image_sha256=fingerprint)
            session.add(generation)
            await session.commit()
            return generation.id

    async def test_concurrent_display_adds_one_tile(self):
        generation_id = await self.add_generation()
        async def display():
            async with SessionLocal() as session:
                return await display_on_dome(DomeDisplayRequest(generation_id=generation_id), None, session)
        with patch("app.api.routes.dome.hub.broadcast", new_callable=AsyncMock) as broadcast:
            results = await asyncio.gather(*(display() for _ in range(10)))
        self.assertEqual(len({result.id for result in results}), 1)
        self.assertEqual(broadcast.await_count, 1)
        async with SessionLocal() as session:
            self.assertEqual(await session.scalar(select(func.count(DomeItem.id))), 1)

    async def test_snapshot_and_preview_exclude_duplicate_pixels_and_prompts(self):
        ids = [await self.add_generation("first", "a" * 64),
               await self.add_generation("different prompt same pixels", "a" * 64),
               await self.add_generation("  FIRST  ", "b" * 64),
               await self.add_generation("second", "c" * 64)]
        async with SessionLocal() as session:
            session.add_all(DomeItem(generation_id=generation_id, position=index) for index, generation_id in enumerate(ids))
            await session.commit()
            snapshot = await _load_items(session)
            preview = await dome_preview(session)
        self.assertEqual([item.generation_id for item in snapshot], [ids[0], ids[3]])
        self.assertEqual(preview.total, 2)
        self.assertEqual([item.id for item in preview.items], [item.id for item in snapshot])


class SubjectPaginationTests(unittest.TestCase):
    def test_repeated_subject_variants_get_separate_pages_without_losing_images(self):
        from app.schemas import DomeItemOut
        from app.services.canvas import paginate, subject_key
        prompts = manifest()["prompts"]
        # Three subjects in five visual variants: requires five pages, each with three images.
        subset = [prompts[variant * 100 + subject] for variant in range(5) for subject in range(3)]
        items = [DomeItemOut(id=index, generation_id=uuid.uuid4(), image_key=str(index),
                             url="/image", thumb_url="/thumb", prompt=prompt, position=index,
                             created_at=datetime.now(timezone.utc)) for index, prompt in enumerate(subset)]
        output = paginate(items, 50)
        self.assertEqual({item.id for item in output}, {item.id for item in items})
        self.assertEqual(max(item.page_index for item in output), 4)
        for page in range(5):
            group = [item for item in output if item.page_index == page]
            self.assertEqual(len(group), 3)
            self.assertEqual(len({subject_key(item.prompt) for item in group}), 3)
        self.assertEqual([item.id for item in output], [item.id for item in paginate(items, 50)])

    def test_full_manifest_page_capacity_and_no_subject_repetition(self):
        from app.schemas import DomeItemOut
        from app.services.canvas import paginate, subject_key
        items = [DomeItemOut(id=index, generation_id=uuid.uuid4(), image_key=str(index),
                             url="/image", thumb_url="/thumb", prompt=prompt, position=index,
                             created_at=datetime.now(timezone.utc))
                 for index, prompt in enumerate(manifest()["prompts"])]
        output = paginate(items, 50)
        self.assertEqual(len(output), 500)
        self.assertEqual(max(item.page_index for item in output), 9)
        for page in range(10):
            group = [item for item in output if item.page_index == page]
            self.assertEqual(len(group), 50)
            self.assertEqual(len({subject_key(item.prompt) for item in group}), 50)


if __name__ == "__main__":
    unittest.main()
