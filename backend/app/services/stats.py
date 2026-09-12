"""Сводка регистраций для админки.

Считаем по анкетам участников: страна и дата рождения есть только там, а анкета
заводится тем же действием, что и учётка, — значит одна анкета равна одной
регистрации.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Participant
from app.services.registration import age_on

PERIOD = timedelta(hours=24)

# Границы возрастных корзин берём по нижнему краю: «18–35» включает восемнадцатилетних,
# «35+» — тех, кому уже исполнилось 35.
ADULT_AGE = 18
SENIOR_AGE = 35


@dataclass(slots=True)
class RegistrationStats:
    since: datetime
    total: int
    # Пары «страна, сколько раз» — от частых к редким.
    by_country: list[tuple[str, int]]
    under_18: int
    from_18_to_35: int
    over_35: int


async def collect(session: AsyncSession, now: datetime) -> RegistrationStats:
    since = now - PERIOD
    rows = (
        await session.execute(
            select(Participant.country, Participant.birth_date).where(
                Participant.created_at >= since
            )
        )
    ).all()

    today = now.date()
    # Страну гость вписывает руками, поэтому «Россия» и «россия » — одно и то же.
    # Ключ приводим к нижнему регистру, а показываем написание, встреченное первым.
    countries: dict[str, tuple[str, int]] = {}
    under_18 = from_18_to_35 = over_35 = 0

    for country, birth_date in rows:
        label = " ".join(country.split())
        written, count = countries.get(label.casefold(), (label, 0))
        countries[label.casefold()] = (written, count + 1)

        age = age_on(birth_date, today)
        if age < ADULT_AGE:
            under_18 += 1
        elif age < SENIOR_AGE:
            from_18_to_35 += 1
        else:
            over_35 += 1

    return RegistrationStats(
        since=since,
        total=len(rows),
        by_country=sorted(
            countries.values(), key=lambda item: (-item[1], item[0].casefold())
        ),
        under_18=under_18,
        from_18_to_35=from_18_to_35,
        over_35=over_35,
    )
