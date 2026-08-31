import secrets

from fastapi import Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models import User
from app.services.access import get_state, get_user_by_email, normalize_email
from app.services.provod import ProvodClient
from app.services.registration import get_participant


def require_admin_token(token: str = Query(default="")) -> str:
    """Админка открывается по ссылке с токеном, как и сам экран холста."""
    if not secrets.compare_digest(token, get_settings().admin_token):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен администратора.",
        )
    return token


def get_provod(request: Request) -> ProvodClient:
    """Один httpx-клиент на приложение, создаётся в lifespan."""
    return request.app.state.provod


async def require_access_email(
    x_access_email: str = Header(default=""),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Почта приходит заголовком X-Access-Email и служит единственным признаком участника."""
    user = await get_user_by_email(session, normalize_email(x_access_email))
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Эта почта не зарегистрирована.",
        )
    return user


async def require_participant(
    user: User = Depends(require_access_email),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Без анкеты и обеих отметок ввод промпта невозможен — требование экрана 1."""
    if await get_participant(session, user) is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Сначала заполните анкету участника и подтвердите согласия.",
        )
    return user


async def require_quota(
    user: User = Depends(require_participant),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Пускаем к генерации, только пока у кода остались попытки."""
    state = await get_state(session, user)
    if state.remaining <= 0:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Генерации по этой почте закончились ({state.used} из {state.limit})."
            ),
        )
    return user
