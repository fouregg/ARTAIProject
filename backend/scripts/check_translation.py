"""Проверка перевода на 7 языках без трат на генерацию изображений.

Запуск из каталога backend/:
    ../.venv/bin/python -m scripts.check_translation
"""

import asyncio
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.services.provod import ProvodClient  # noqa: E402

SAMPLES = {
    "ru": "рыжий кот в скафандре на фоне туманности",
    "en": "a ginger cat in a spacesuit against a nebula",
    "zh": "一只穿着宇航服的橘猫，背景是星云",
    "fr": "un chat roux en combinaison spatiale devant une nébuleuse",
    "es": "un gato naranja con traje espacial frente a una nebulosa",
    "pt": "um gato ruivo de fato espacial diante de uma nebulosa",
    "ar": "قط برتقالي يرتدي بدلة فضاء أمام سديم",
}


async def main() -> int:
    settings = get_settings()
    failures = 0

    async with httpx.AsyncClient(
        base_url=settings.provod_base_url,
        headers={
            "Authorization": f"Bearer {settings.provod_api_key}",
            "Content-Type": "application/json",
        },
    ) as http:
        client = ProvodClient(http)
        print(f"Модель перевода: {settings.provod_text_model}\n")

        for expected_lang, text in SAMPLES.items():
            result = await client.translate(text, None)
            mark = "OK " if not result.degraded else "FAIL"
            if result.degraded:
                failures += 1
            lang_note = "" if result.detected_lang == expected_lang else f" (ожидали {expected_lang})"
            print(f"[{mark}] {expected_lang}: определён {result.detected_lang}{lang_note}")
            print(f"       {text}")
            print(f"    -> {result.prompt_en}\n")

    print("Все переводы прошли" if not failures else f"Провалов: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
