from datetime import datetime
from typing import Optional

import pendulum
from sqlalchemy import DateTime, ForeignKey, sql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class TimestampMixin:
    """Mixin to add created_at and updated_at fields to ORM models."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=sql.func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=sql.func.now())


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class Activity(TimestampMixin, Base):
    """Represents an activity type (e.g., mining, woodcutting)."""

    __tablename__ = "activities"

    activity_id: Mapped[int] = mapped_column(primary_key=True)
    activity_name: Mapped[str] = mapped_column(unique=True)
    activity_type: Mapped[str]

    options: Mapped[list["ActivityOption"]] = relationship("ActivityOption")

    def __str__(self) -> str:
        return f"{self.activity_name}"


class ActivityOption(TimestampMixin, Base):
    """Represents a specific option for an activity (e.g., iron for mining)."""

    __tablename__ = "activity_options"

    activity_option_id: Mapped[int] = mapped_column(primary_key=True)
    activity_option_name: Mapped[str] = mapped_column(unique=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.activity_id"))
    action_time: Mapped[int]
    reward_item_id: Mapped[int] = mapped_column(ForeignKey("items.item_id"))
    reward_experience: Mapped[int]

    activity = relationship("Activity", back_populates="options")
    reward_item = relationship("Item")


class Item(TimestampMixin, Base):
    """Represents an item in the game."""

    __tablename__ = "items"

    item_id: Mapped[int] = mapped_column(primary_key=True)
    item_name: Mapped[str] = mapped_column(unique=True)


class CharacterItem(TimestampMixin, Base):
    """Represents an item owned by a character."""

    __tablename__ = "character_items"

    character_item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.character_id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.item_id"))
    quantity: Mapped[int] = mapped_column(default=0)

    character: Mapped["Character"] = relationship("Character")
    item: Mapped[Item] = relationship("Item")


class CharacterActivity(TimestampMixin, Base):
    """Represents an activity currently or previously performed by a character."""

    __tablename__ = "character_activities"

    character_activity_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.character_id"))
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.activity_id"))
    activity_option_id: Mapped[int] = mapped_column(ForeignKey("activity_options.activity_option_id"))

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=sql.func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    activity: Mapped["Activity"] = relationship("Activity")
    activity_option: Mapped["ActivityOption"] = relationship("ActivityOption")
    character: Mapped["Character"] = relationship("Character", back_populates="activities")

    def __str__(self) -> str:
        return f"""{self.activity.activity_name}\n            \tStart Time: {self.started_at} ({pendulum.instance(self.started_at).diff_for_humans()})\
        """


class Character(TimestampMixin, Base):
    """Represents a player character."""

    __tablename__ = "characters"

    character_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_name: Mapped[str] = mapped_column(unique=True)

    skills: Mapped[list["CharacterSkill"]] = relationship(
        "CharacterSkill", uselist=True, back_populates="character", lazy="selectin"
    )
    activities: Mapped[list["CharacterActivity"]] = relationship(
        "CharacterActivity", uselist=True, back_populates="character", lazy="selectin"
    )

    items: Mapped[list["CharacterItem"]] = relationship("CharacterItem", uselist=True, overlaps="character")


class CharacterSkill(TimestampMixin, Base):
    """Represents a skill and experience for a character."""

    __tablename__ = "character_skills"

    character_skill_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.character_id"))
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.activity_id"))
    experience: Mapped[int] = mapped_column(default=0)

    character: Mapped["Character"] = relationship("Character", back_populates="skills")


def ensure_utc(dt):
    """Ensure a datetime is timezone-aware in UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return pendulum.instance(dt, tz="UTC")
    return dt
