from datetime import datetime
from typing import Optional

import pendulum
from sqlalchemy import ForeignKey, sql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Activity(Base):
    __tablename__ = "activities"

    activity_id: Mapped[int] = mapped_column(primary_key=True)
    activity_name: Mapped[str] = mapped_column(unique=True)
    activity_type: Mapped[str]

    def __str__(self) -> str:
        return f"{self.activity_name}"


class Item(Base):
    __tablename__ = "items"

    item_id: Mapped[int] = mapped_column(primary_key=True)
    item_name: Mapped[str] = mapped_column(unique=True)


class ActivityAction(Base):
    __tablename__ = "activity_actions"

    activity_action_id: Mapped[int] = mapped_column(primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.activity_id"))
    action_duration: Mapped[int]


class CharacterItem(Base):
    __tablename__ = "character_items"

    character_item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.character_id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.item_id"))
    quantity: Mapped[int]

    created_at: Mapped[datetime] = mapped_column(default=sql.func.now())
    updated_at: Mapped[datetime] = mapped_column(default=sql.func.now())

    character: Mapped["Character"] = relationship("Character")
    item: Mapped[Item] = relationship("Item")


class CharacterActivity(Base):
    """
    Activity for a character.
    """

    __tablename__ = "character_activities"

    character_activity_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.character_id"))
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.activity_id"))
    started_at: Mapped[datetime] = mapped_column(default=sql.func.now())
    ended_at: Mapped[Optional[datetime]]

    activity: Mapped["Activity"] = relationship("Activity")
    character: Mapped["Character"] = relationship("Character", back_populates="activities")

    def stop(self) -> None:
        self.end_time = pendulum.now("UTC")

    def __str__(self) -> str:
        return f"""{self.activity.activity_name}
            \tStart Time: {self.started_at} ({pendulum.instance(self.started_at).diff_for_humans()})\
        """


class Character(Base):
    __tablename__ = "characters"

    character_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_name: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=sql.func.now())

    skills: Mapped[list["CharacterSkill"]] = relationship(
        "CharacterSkill", uselist=True, back_populates="character", lazy="selectin"
    )
    activities: Mapped[list["CharacterActivity"]] = relationship(
        "CharacterActivity", uselist=True, back_populates="character", lazy="selectin"
    )


class CharacterSkill(Base):
    __tablename__ = "character_skills"

    character_skill_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.character_id"))
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.activity_id"))
    experience: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=sql.func.now())
    updated_at: Mapped[datetime] = mapped_column(default=sql.func.now())

    character: Mapped["Character"] = relationship("Character", back_populates="skills")
