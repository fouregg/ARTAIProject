"""Юридические тексты, которые терминал показывает до акцепта.

Пункт 12.1 Соглашения требует хранить редакцию и хеш-сумму предъявленных текстов,
поэтому тексты лежат файлами, а хеш считается от их содержимого. Правка файла меняет
хеш — старые акцепты остаются привязанными к своей редакции.
"""

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.config import PROJECT_ROOT

LEGAL_DIR = Path(__file__).resolve().parents[1] / "legal"

# Меняйте вручную, когда меняется сам текст: хеш поймает правку, а версия — её описание.
AGREEMENT_VERSION = "1.0"
CONSENT_VERSION = "1.0"

# Политика — 32-страничный PDF, показываем ссылкой, а не текстом на экране.
POLICY_FILE = PROJECT_ROOT / "docs" / "3-Политика обработки ПДН.pdf"
POLICY_URL = "/api/legal/policy.pdf"

# Экранные тексты терминала — дословно из документа «4-Экранные тексты терминала».
CHECKBOX_AGREEMENT = (
    "Я подтверждаю, что запрос составлен мной и не нарушает прав других людей, "
    "и разрешаю показать созданное изображение на общем экране выставки и использовать "
    "его вместе с моим запросом. Изображение станет частью общей композиции."
)
CHECKBOX_CONSENT = (
    "Я даю согласие на обработку моих персональных данных для отчетности организатора, "
    "статистики и подтверждения возраста. Данные не показываются публично."
)
AGE_NOTICE = (
    "Дети младше 14 лет пользуются сервисом только вместе со взрослым. "
    "За участника младше 18 лет отметку ставит родитель или другой законный представитель."
)
REJECTION_NOTICE = "Запрос не может быть обработан. Попробуйте сформулировать его иначе."
AI_DISCLOSURE = "Изображение создано с использованием искусственного интеллекта."


@dataclass(frozen=True, slots=True)
class LegalDocument:
    key: str
    title: str
    version: str
    sha256: str
    text: str


def _load(key: str, title: str, filename: str, version: str) -> LegalDocument:
    text = (LEGAL_DIR / filename).read_text(encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return LegalDocument(key=key, title=title, version=version, sha256=digest, text=text)


@lru_cache
def get_agreement() -> LegalDocument:
    return _load(
        "agreement",
        "Пользовательское соглашение",
        "agreement.txt",
        AGREEMENT_VERSION,
    )


@lru_cache
def get_consent() -> LegalDocument:
    return _load(
        "consent",
        "Согласие на обработку персональных данных",
        "consent.txt",
        CONSENT_VERSION,
    )


def documents() -> list[LegalDocument]:
    return [get_agreement(), get_consent()]
