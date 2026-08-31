"""Учётки: вход по электронной почте и подсчёт оставшихся генераций.

Почта здесь одновременно и логин, и единственный признак участника: пароля нет,
письма с подтверждением не отправляются. Поэтому вход ограничен по частоте —
см. LoginRateLimiter, иначе чужую квоту можно было бы израсходовать, просто зная адрес.
"""

import logging
import re
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Generation, User

logger = logging.getLogger(__name__)

EMAIL_MAX_LENGTH = 255
# Намеренно нестрогая проверка: задача — отсечь опечатки, а не пересказать RFC 5322.
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")

# Вход: не больше 10 попыток с одного адреса за минуту.
LOGIN_ATTEMPTS = 10
LOGIN_WINDOW_SECONDS = 60


@dataclass(slots=True)
class AccessState:
    email: str
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


def normalize_email(raw: str) -> str:
    """Приводим к одному виду: пробелы по краям и регистр не должны создавать учётки-двойники."""
    return raw.strip().lower()


def is_valid_email(email: str) -> bool:
    return len(email) <= EMAIL_MAX_LENGTH and EMAIL_PATTERN.match(email) is not None


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    if not is_valid_email(email):
        return None
    return await session.scalar(
        select(User).where(User.email == email, User.is_active.is_(True))
    )


async def get_or_create_user(session: AsyncSession, email: str) -> User:
    """Учётка заводится в момент регистрации: отдельного шага «создать аккаунт» нет."""
    user = await get_user_by_email(session, email)
    if user is not None:
        return user

    user = User(
        email=email,
        display_name=email,
        generations_limit=get_settings().code_generations_limit,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user


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
        email=user.email or "",
        limit=user.generations_limit,
        used=await count_used(session, user),
    )


async def touch(session: AsyncSession, user: User) -> None:
    user.last_used_at = datetime.now(timezone.utc)
    await session.commit()
