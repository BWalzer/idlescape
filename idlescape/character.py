from typing import Optional
import sqlalchemy.orm
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship, selectinload
from sqlalchemy import ForeignKey
from sqlalchemy import sql
from datetime import datetime
import os
import pendulum
import json

from idlescape.session_manager import get_session, ENGINE


class Base(DeclarativeBase):
    pass


class Activity(Base):
    __tablename__ = "activities"

    activity_id: Mapped[int] = mapped_column(primary_key=True)
    activity_name: Mapped[str] = mapped_column(unique=True)
    activity_type: Mapped[str]

    @classmethod
    def load_activities(cls):
        # Drop the activities table
        Base.metadata.drop_all(bind=ENGINE, tables=[Activity.__table__])
        # Recreate the activities table
        Base.metadata.create_all(bind=ENGINE, tables=[Activity.__table__])
        with open("activities.json", "r") as f:
            activities = json.load(f)

        with get_session() as session:
            for activity in activities:
                session.add(Activity(**activity))
            session.commit()

    @classmethod
    def get_activity_by_name(cls, activity_name) -> Optional["Activity"]:
        with get_session() as session:
            return session.query(cls).filter_by(activity_name=activity_name).one()

    def __str__(self) -> str:
        return f"{self.activity_name}"


class CharacterActivity(Base):
    """
    Activity for a character.
    """

    __tablename__ = "character_activities"

    character_activity_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # type: ignore
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.character_id"))  # type: ignore
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.activity_id"))
    start_time: Mapped[datetime] = mapped_column(default=sql.func.now())
    end_time: Mapped[Optional[datetime]]

    activity: Mapped["Activity"] = relationship("Activity")
    character: Mapped["Character"] = relationship("Character", back_populates="activities")  # type: ignore

    def stop(self) -> None:
        self.end_time = pendulum.now("UTC")

    def __str__(self) -> str:
        return f"""{self.activity.activity_name}
            \tStart Time: {self.start_time} ({pendulum.instance(self.start_time).diff_for_humans()})\
        """


class Character(Base):
    __tablename__ = "characters"

    character_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # type: ignore
    character_name: Mapped[str] = mapped_column(unique=True)  # type: ignore
    created_at_utc: Mapped[datetime] = mapped_column(default=sql.func.now())

    activities: Mapped[list["CharacterActivity"]] = relationship(
        "CharacterActivity", uselist=True, back_populates="character", lazy="selectin"
    )

    @property
    def current_activity(self) -> Optional[CharacterActivity]:
        unended_activities: list[Activity] = [activity for activity in self.activities if activity.end_time is None]
        if len(unended_activities) > 1:
            raise ValueError(f"Character '{self.character_name}' has multiple unended activities. This is bad. ")
        if not unended_activities:
            return None
        return unended_activities[0]

    @classmethod
    def get_character_by_name(cls, character_name: str) -> Optional["Character"]:
        """
        Search the database for a Character, by name.

        Returns None if a character isn't found.
        """
        with get_session() as session:
            return (
                session.query(cls)
                .options(selectinload(cls.activities))
                # .options(selectinload(cls.current_activity))
                .filter_by(character_name=character_name)
                .one()
            )

    def start_activity(self, activity: Activity) -> None:
        self.activities.append(CharacterActivity(activity.activity_id, self.character_id))
        self.save()

    def stop_current_activity(self) -> None:
        with get_session() as session:  # noqa
            if not self.current_activity:
                raise ValueError(f"Character '{self.character_name}' has no current activity to stop.")
            self.current_activity.stop()
            self.save()

    def __str__(self) -> str:
        # TODO: Make this prettier, colors, bold, etc.
        return f"""\
            Name: {self.character_name}
            Created: {self.created_at_utc}
            Current Activity: {self.current_activity}\
        """

    def save(self) -> None:
        with get_session() as session:
            session.add(self)


def _init_db():
    if os.path.exists("idlescape.db"):
        os.remove("idlescape.db")
    engine = sqlalchemy.create_engine("sqlite:///idlescape.db")

    Base.metadata.create_all(engine)


if __name__ == "__main__":
    _init_db()
