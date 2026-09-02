import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _now_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class User(Base):
    """Учётка = 5-значный код доступа.

    Посетитель вводит код и получает `generations_limit` генераций на него — навсегда,
    без суточного сброса. Служебная запись `default` кода не имеет: к ней привязаны
    генерации, сделанные до появления авторизации.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str | None] = mapped_column(String(5), unique=True, nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    generations_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = _now_column()
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    generations: Mapped[list["Generation"]] = relationship(back_populates="user")


class Generation(Base):
    """Журнал каждой генерации — в том числе неуспешной. Основа будущего подсчёта квот."""

    __tablename__ = "generations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    prompt_original: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_translated: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_lang: Mapped[str | None] = mapped_column(String(8), nullable=True)
    detected_lang: Mapped[str | None] = mapped_column(String(8), nullable=True)
    translation_degraded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    model: Mapped[str] = mapped_column(String(120), nullable=False)
    size: Mapped[str] = mapped_column(String(32), nullable=False)
    quality: Mapped[str] = mapped_column(String(16), nullable=False)
    output_format: Mapped[str] = mapped_column(String(8), nullable=False, default="png")

    # Какие категории модерации сработали — по ним отвечают на возражение (п. 8.1).
    moderation_categories: Mapped[str | None] = mapped_column(String(255), nullable=True)

    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = _now_column()

    user: Mapped[User] = relationship(back_populates="generations")


class GalleryItem(Base):
    """Сохранение в галерею — отдельная запись, независимая от отправки на купол."""

    __tablename__ = "gallery_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    generation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("generations.id", ondelete="CASCADE"), unique=True, index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # True — картинка попала в галерею сама, сразу после генерации. Такие записи
    # не удерживают файл от уборки: иначе срок хранения перестал бы работать вовсе.
    is_auto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = _now_column()

    generation: Mapped[Generation] = relationship()


class DomeItem(Base):
    """Плитки коллажа на купольном экране. Купол восстанавливает мозаику отсюда."""

    __tablename__ = "dome_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    generation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("generations.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = _now_column()

    generation: Mapped[Generation] = relationship()


class Participant(Base):
    """Анкета участника: экран 1 терминала. Одна анкета на один код доступа."""

    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )

    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    country: Mapped[str] = mapped_column(String(120), nullable=False)

    # Отметка законного представителя: обязательна для участников младше 18 лет (п. 11.2).
    is_legal_representative: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_at: Mapped[datetime] = _now_column()

    user: Mapped[User] = relationship()


class Consent(Base):
    """Фиксация акцепта по пункту 12.1 Соглашения.

    На каждый предъявленный документ — своя запись с редакцией и хеш-суммой текста,
    который человек видел на экране в момент нажатия.
    """

    __tablename__ = "consents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    participant_id: Mapped[int] = mapped_column(
        ForeignKey("participants.id", ondelete="CASCADE"), index=True
    )

    document_key: Mapped[str] = mapped_column(String(32), nullable=False)
    document_version: Mapped[str] = mapped_column(String(16), nullable=False)
    document_sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    terminal_id: Mapped[str] = mapped_column(String(64), nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    ui_language: Mapped[str] = mapped_column(String(8), nullable=False, default="ru")
    accepted_at: Mapped[datetime] = _now_column()
