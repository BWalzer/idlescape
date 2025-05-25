from typing import Optional
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey
from sqlalchemy import sql
from datetime import datetime
import pendulum


class Base(DeclarativeBase):
    pass


class Activity(Base):
    __tablename__ = "activities"

    activity_id: Mapped[int] = mapped_column(primary_key=True)
    activity_name: Mapped[str] = mapped_column(unique=True)
    activity_type: Mapped[str]

    def __str__(self) -> str:
        return f"{self.activity_name}"


class CharacterActivity(Base):
    """
    Activity for a character.
    """

    __tablename__ = "character_activities"

    character_activity_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.character_id"))
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.activity_id"))
    start_time: Mapped[datetime] = mapped_column(default=sql.func.now())
    end_time: Mapped[Optional[datetime]]

    activity: Mapped["Activity"] = relationship("Activity")
    character: Mapped["Character"] = relationship("Character", back_populates="activities")

    def stop(self) -> None:
        self.end_time = pendulum.now("UTC")

    def __str__(self) -> str:
        return f"""{self.activity.activity_name}
            \tStart Time: {self.start_time} ({pendulum.instance(self.start_time).diff_for_humans()})\
        """


class Character(Base):
    __tablename__ = "characters"

    character_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_name: Mapped[str] = mapped_column(unique=True)
    created_at_utc: Mapped[datetime] = mapped_column(default=sql.func.now())

    activities: Mapped[list["CharacterActivity"]] = relationship(
        "CharacterActivity", uselist=True, back_populates="character", lazy="selectin"
    )

    def __str__(self) -> str:
        # TODO: Make this prettier, colors, bold, etc.
        return f"""\
            Name: {self.character_name}
            Created: {self.created_at_utc}
            Current Activity: {self.current_activity}\
        """
