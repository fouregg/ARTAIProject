"""Учётки-коды: выпуск, вход и подсчёт оставшихся генераций.

Код из 5 цифр — это и логин, и пароль одновременно, поэтому пространство кодов
маленькое (100 000). Чтобы его нельзя было перебрать, вход ограничен по частоте:
см. LoginRateLimiter ниже. Для публичной установки этого достаточно, для интернета —
стоит добавить капчу или удлинить код.
"""

import logging
import secrets
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Generation, User

logger = logging.getLogger(__name__)

CODE_LENGTH = 5
CODE_SPACE = 10**CODE_LENGTH
DEFAULT_CODE_LIMIT = 10

# Вход: не больше 10 попыток с одного адреса за минуту.
LOGIN_ATTEMPTS = 10
LOGIN_WINDOW_SECONDS = 60


@dataclass(slots=True)
class AccessState:
    code: str
    limit: int
    used: int

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.used)


class LoginRateLimiter:
    """Скользящее окно попыток входа по адресу клиента. Живёт в памяти процесса."""

    def __init__(self) -> None:
        self._attempts: dict[str, deque[float]] = {}

    def allow(self, client: str) -> bool:
        now = time.monotonic()
        window = self._attempts.setdefault(client, deque())

        while window and now - window[0] > LOGIN_WINDOW_SECONDS:
            window.popleft()

        if len(window) >= LOGIN_ATTEMPTS:
            return False

        window.append(now)
        return True

    def reset(self, client: str) -> None:
        """После удачного входа счётчик обнуляем — честного гостя ограничивать незачем."""
        self._attempts.pop(client, None)


login_limiter = LoginRateLimiter()


def normalize_code(raw: str) -> str:
    """Убираем пробелы и дефисы: код часто диктуют или печатают на билете."""
    return "".join(ch for ch in raw if ch.isdigit())


def is_valid_format(code: str) -> bool:
    return len(code) == CODE_LENGTH and code.isdigit()


async def get_user_by_code(session: AsyncSession, code: str) -> User | None:
    if not is_valid_format(code):
        return None
    return await session.scalar(
        select(User).where(User.code == code, User.is_active.is_(True))
    )


async def count_used(session: AsyncSession, user: User) -> int:
    """Неудачные генерации в лимит не засчитываем — гость за них не платил."""
    used = await session.scalar(
        select(func.count(Generation.id)).where(
            Generation.user_id == user.id,
            Generation.status != "error",
        )
    )
    return used or 0


async def get_state(session: AsyncSession, user: User) -> AccessState:
    return AccessState(
        code=user.code or "",
        limit=user.generations_limit,
        used=await count_used(session, user),
    )


async def touch(session: AsyncSession, user: User) -> None:
    user.last_used_at = datetime.now(timezone.utc)
    await session.commit()


async def create_codes(
    session: AsyncSession,
    count: int,
    limit: int = DEFAULT_CODE_LIMIT,
) -> list[str]:
    """Выпускает `count` новых уникальных кодов. Рассчитано и на 10 000 штук за раз."""
    if count <= 0:
        return []

    taken = set(
        (await session.scalars(select(User.code).where(User.code.is_not(None)))).all()
    )
    if len(taken) + count > CODE_SPACE:
        raise ValueError(
            f"Столько кодов не выпустить: всего возможно {CODE_SPACE}, "
            f"занято {len(taken)}."
        )

    fresh: list[str] = []
    while len(fresh) < count:
        code = f"{secrets.randbelow(CODE_SPACE):0{CODE_LENGTH}d}"
        if code in taken:
            continue
        taken.add(code)
        fresh.append(code)

    session.add_all(
        [
            User(
                code=code,
                display_name=f"code-{code}",
                generations_limit=limit,
                is_active=True,
            )
            for code in fresh
        ]
    )
    await session.commit()
    logger.info("Выпущено кодов: %s (лимит %s генераций на код)", len(fresh), limit)
    return fresh
