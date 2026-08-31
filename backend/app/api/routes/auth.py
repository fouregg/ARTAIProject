from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_access_email
from app.db import get_session
from app.models import User
from app.schemas import AccessStateOut, LoginRequest, RegisterRequest
from app.services.access import (
    AccessState,
    get_state,
    get_user_by_email,
    is_valid_email,
    login_limiter,
    normalize_email,
    touch,
)
from app.services.registration import RegistrationError, get_participant, register

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _to_out(state: AccessState, registered: bool) -> AccessStateOut:
    return AccessStateOut(
        email=state.email,
        limit=state.limit,
        used=state.used,
        remaining=state.remaining,
        registered=registered,
    )


async def _state_out(session: AsyncSession, user: User) -> AccessStateOut:
    participant = await get_participant(session, user)
    return _to_out(await get_state(session, user), participant is not None)


@router.post("/login", response_model=AccessStateOut)
async def login(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> AccessStateOut:
    # Пароля нет, поэтому перебор адресов ограничиваем по адресу клиента.
    client = request.client.host if request.client else "unknown"
    if not login_limiter.allow(client):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много попыток. Подождите минуту и попробуйте снова.",
        )

    email = normalize_email(payload.email)
    if not is_valid_email(email):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Проверьте адрес почты.",
        )

    user = await get_user_by_email(session, email)
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Эта почта не зарегистрирована.",
        )

    login_limiter.reset(client)
    await touch(session, user)
    return await _state_out(session, user)


@router.get("/me", response_model=AccessStateOut)
async def me(
    user: User = Depends(require_access_email),
    session: AsyncSession = Depends(get_session),
) -> AccessStateOut:
    """Фронт зовёт при загрузке: учётку могли отключить или её лимит уже исчерпан."""
    return await _state_out(session, user)


@router.post("/register", response_model=AccessStateOut, status_code=status.HTTP_201_CREATED)
async def register_participant(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> AccessStateOut:
    """Экран 1: почта, анкета участника и обе обязательные отметки.

    Учётка заводится здесь же — отдельного шага «создать аккаунт» нет.
    """
    try:
        user = await register(session, payload, date.today())
    except RegistrationError as exc:
        raise HTTPException(exc.status, detail=exc.message) from exc

    return await _state_out(session, user)
