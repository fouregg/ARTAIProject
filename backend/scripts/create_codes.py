"""Выпуск кодов доступа.

Запуск из каталога backend/:
    ../.venv/bin/python -m scripts.create_codes            # 10 кодов
    ../.venv/bin/python -m scripts.create_codes --count 10000
    ../.venv/bin/python -m scripts.create_codes --count 100 --limit 3 --quiet

--quiet печатает только количество: список из 10 000 кодов удобнее забрать из БД
    select code from users where code is not null order by created_at desc;
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.db import SessionLocal, engine  # noqa: E402
from app.services.access import create_codes  # noqa: E402


async def main() -> int:
    settings = get_settings()

    parser = argparse.ArgumentParser(description="Выпустить коды доступа")
    parser.add_argument("--count", type=int, default=10, help="сколько кодов выпустить")
    parser.add_argument(
        "--limit",
        type=int,
        default=settings.code_generations_limit,
        help="сколько генераций даёт каждый код",
    )
    parser.add_argument("--quiet", action="store_true", help="не печатать сами коды")
    args = parser.parse_args()

    try:
        async with SessionLocal() as session:
            codes = await create_codes(session, args.count, args.limit)
    finally:
        await engine.dispose()

    print(f"Выпущено кодов: {len(codes)}, по {args.limit} генераций на каждый")
    if not args.quiet:
        for code in codes:
            print(f"  {code}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
