"""Экран 1: анкета участника и фиксация акцепта.

Правила взяты из Пользовательского соглашения и документа с экранными текстами:
  * без обеих отметок ввод промпта невозможен;
  * за участника младше 18 лет отметку ставит законный представитель (п. 11.2, 11.5);
  * на каждый предъявленный документ сохраняется редакция и хеш текста (п. 12.1).
"""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Consent, Participant, User
from app.schemas import RegisterRequest
from app.services import legal
from app.services.access import get_or_create_user, is_valid_email, normalize_email

ADULT_AGE = 18
MAX_AGE = 120
REQUIRED_DOCUMENTS = ("agreement", "consent")


class RegistrationError(Exception):
    """Ошибка анкеты с готовым текстом для экрана."""

    def __init__(self, message: str, *, status: int = 422) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


def age_on(born: date, today: date) -> int:
    years = today.year - born.year
    if (today.month, today.day) < (born.month, born.day):
        years -= 1
    return years


def _validate_documents(request: RegisterRequest) -> None:
    """Сверяем, что человек принял именно те тексты, которые сейчас на экране."""
    accepted = {item.key: item for item in request.accepted}

    for key in REQUIRED_DOCUMENTS:
        if key not in accepted:
            raise RegistrationError(
                "Чтобы продолжить, отметьте оба согласия.",
            )

    current = {"agreement": legal.get_agreement(), "consent": legal.get_consent()}
    for key, document in current.items():
        item = accepted[key]
        if item.sha256 != document.sha256 or item.version != document.version:
            raise RegistrationError(
                "Тексты соглашений обновились. Перезагрузите страницу и подтвердите заново.",
                status=409,
            )


def _validate_person(request: RegisterRequest, today: date) -> None:
    if request.birth_date > today:
        raise RegistrationError("Проверьте дату рождения.")

    age = age_on(request.birth_date, today)
    if age > MAX_AGE:
        raise RegistrationError("Проверьте дату рождения.")

    # Пункты 11.2 и 11.5: без отметки представителя несовершеннолетний не допускается.
    if age < ADULT_AGE and not request.is_legal_representative:
        raise RegistrationError(legal.AGE_NOTICE)


async def get_participant(session: AsyncSession, user: User) -> Participant | None:
    return await session.scalar(
        select(Participant).where(Participant.user_id == user.id)
    )


async def register(
    session: AsyncSession,
    request: RegisterRequest,
    today: date,
) -> User:
    """Заводит учётку по почте и анкету к ней. Возвращает учётку участника."""
    email = normalize_email(request.email)
    if not is_valid_email(email):
        raise RegistrationError("Проверьте адрес почты.")

    _validate_documents(request)
    _validate_person(request, today)

    user = await get_or_create_user(session, email)
    if await get_participant(session, user) is not None:
        raise RegistrationError("Эта почта уже зарегистрирована — просто войдите.", status=409)

    participant = Participant(
        user_id=user.id,
        last_name=request.last_name.strip(),
        first_name=request.first_name.strip(),
        middle_name=(request.middle_name or "").strip() or None,
        birth_date=request.birth_date,
        country=request.country.strip(),
        is_legal_representative=request.is_legal_representative,
    )
    session.add(participant)
    await session.flush()

    session_id = uuid.uuid4()
    terminal_id = get_settings().terminal_id
    session.add_all(
        [
            Consent(
                user_id=user.id,
                participant_id=participant.id,
                document_key=document.key,
                document_version=document.version,
                document_sha256=document.sha256,
                terminal_id=terminal_id,
                session_id=session_id,
                ui_language=request.ui_language,
            )
            for document in legal.documents()
        ]
    )
    await session.commit()
    await session.refresh(user)

    return user
