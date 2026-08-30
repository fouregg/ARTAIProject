from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import User
from app.services.access import get_state, get_user_by_code, normalize_code
from app.services.provod import ProvodClient
from app.services.registration import get_participant


def get_provod(request: Request) -> ProvodClient:
    """Один httpx-клиент на приложение, создаётся в lifespan."""
    return request.app.state.provod


async def require_access_code(
    x_access_code: str = Header(default=""),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Код доступа приходит заголовком X-Access-Code и одновременно служит паролем."""
    user = await get_user_by_code(session, normalize_code(x_access_code))
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Код не найден или больше не действует.",
        )
    return user


async def require_participant(
    user: User = Depends(require_access_code),
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
                f"Генерации по этому коду закончились ({state.used} из {state.limit}). "
                "Введите другой код."
            ),
        )
    return user
