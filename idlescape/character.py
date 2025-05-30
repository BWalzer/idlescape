from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pendulum
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, sql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from idlescape.experience_to_level import xp_to_level


class TimestampMixin:
    """Mixin to add created_at and updated_at fields to ORM models.

    Attributes:
        created_at (datetime): UTC timestamp when the record was created
        updated_at (datetime): UTC timestamp when the record was last updated
    """

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=sql.func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=sql.func.now())


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class Activity(TimestampMixin, Base):
    """Represents an activity type in the game, such as mining or woodcutting.

    An activity is a high-level category of actions that a character can perform.
    Each activity can have multiple options (specific actions) associated with it.

    Attributes:
        activity_id (int): Unique identifier for the activity
        activity_name (str): Unique name of the activity (e.g., "mining")
        activity_type (str): The type of activity (affects game mechanics)
        options (list[ActivityOption]): Related activity options for this activity

    Relationships:
        options: One-to-many relationship to ActivityOption
    """

    __tablename__ = "activities"

    activity_id: Mapped[int] = mapped_column(primary_key=True)
    activity_name: Mapped[str] = mapped_column(unique=True)
    activity_type: Mapped[str]

    def __str__(self) -> str:
        return f"{self.activity_name}"


class ActivityOption(TimestampMixin, Base):
    """Represents a specific option for an activity, such as mining iron ore.

    Activity options are the specific actions that characters can perform within
    an activity category. Each option has its own requirements and rewards.

    Attributes:
        activity_option_id (int): Unique identifier for the activity option
        activity_option_name (str): Unique name of the option (e.g., "iron_ore")
        activity_id (int): Foreign key to parent Activity
        action_time (int): Time in seconds required to complete this action
        skill_requirements (list[ActivityOptionSkillRequirement]): Required skill levels to perform action
        item_costs: (list[ActivityOptionItemCost])


    Relationships:
        activity: Many-to-one relationship to Activity
        reward_item: Many-to-one relationship to Item
    """

    __tablename__ = "activity_options"

    activity_option_id: Mapped[int] = mapped_column(primary_key=True)
    activity_option_name: Mapped[str] = mapped_column(unique=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.activity_id"))
    action_time: Mapped[int]

    activity = relationship("Activity", viewonly=True)
    skill_requirements: Mapped[list["ActivityOptionSkillRequirement"]] = relationship("ActivityOptionSkillRequirement")
    item_costs: Mapped[list["ActivityOptionItemCost"]] = relationship("ActivityOptionItemCost")
    reward_items: Mapped[list["ActivityOptionItemReward"]] = relationship("ActivityOptionItemReward")
    reward_experience: Mapped[list["ActivityOptionExperienceReward"]] = relationship("ActivityOptionExperienceReward")


class ActivityOptionItemReward(TimestampMixin, Base):
    __tablename__ = "activity_option_item_rewards"

    activity_option_item_reward_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    activity_option_id: Mapped[int] = mapped_column(ForeignKey("activity_options.activity_option_id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.item_id"))
    quantity: Mapped[int] = mapped_column(CheckConstraint("quantity > 0"))


class ActivityOptionExperienceReward(TimestampMixin, Base):
    __tablename__ = "activity_option_experience_rewards"

    activity_option_experience_reward_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    activity_option_id: Mapped[int] = mapped_column(ForeignKey("activity_options.activity_option_id"))
    skill_id: Mapped[int] = mapped_column(ForeignKey("activities.activity_id"))
    experience: Mapped[int] = mapped_column(CheckConstraint("experience > 0"))


class ActivityOptionSkillRequirement(TimestampMixin, Base):
    __tablename__ = "activity_option_skill_requirements"

    activity_option_skill_requirement_id: Mapped[int] = mapped_column(primary_key=True)
    activity_option_id: Mapped[int] = mapped_column(ForeignKey("activity_options.activity_option_id"))
    skill_id: Mapped[int] = mapped_column(ForeignKey("activities.activity_id"))
    required_level: Mapped[int] = mapped_column(
        CheckConstraint("required_level between 1 and 99"), default=1, server_default="1"
    )


class ActivityOptionItemCost(TimestampMixin, Base):
    __tablename__ = "activity_option_item_cost"

    activity_option_item_cost_id: Mapped[int] = mapped_column(primary_key=True)
    activity_option_id: Mapped[int] = mapped_column(ForeignKey("activity_options.activity_option_id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.item_id"))
    quantity: Mapped[int] = mapped_column(CheckConstraint("quantity > 0"))


class Item(TimestampMixin, Base):
    """Represents an item that can be obtained in the game.

    Items are rewards from activities and can be stored in a character's inventory.

    Attributes:
        item_id (int): Unique identifier for the item
        item_name (str): Unique name of the item
    """

    __tablename__ = "items"

    item_id: Mapped[int] = mapped_column(primary_key=True)
    item_name: Mapped[str] = mapped_column(unique=True)


class CharacterItem(TimestampMixin, Base):
    """Represents an item in a character's inventory.

    This class tracks the quantity of each item that a character owns.

    Attributes:
        character_item_id (int): Unique identifier for this inventory entry
        character_id (int): Foreign key to the owning Character
        item_id (int): Foreign key to the Item
        quantity (int): Number of this item owned by the character

    Relationships:
        character: Many-to-one relationship to Character
        item: Many-to-one relationship to Item
    """

    __tablename__ = "character_items"

    character_item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.character_id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.item_id"))
    quantity: Mapped[int] = mapped_column(CheckConstraint("quantity >= 0"), default=0, server_default="0")

    character: Mapped["Character"] = relationship("Character")
    item: Mapped[Item] = relationship("Item")


class CharacterActivity(TimestampMixin, Base):
    """Represents an activity being performed by a character.

    Tracks both current and historical activities, with start and end times.
    A character can only have one active (unended) activity at a time.

    Attributes:
        character_activity_id (int): Unique identifier for this activity record
        character_id (int): Foreign key to the Character performing the activity
        activity_id (int): Foreign key to the Activity being performed
        activity_option_id (int): Foreign key to the specific ActivityOption chosen
        started_at (datetime): UTC timestamp when the activity was started

    Relationships:
        activity: Many-to-one relationship to Activity
        activity_option: Many-to-one relationship to ActivityOption
        character: Many-to-one relationship to Character
    """

    __tablename__ = "character_activities"

    character_activity_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.character_id"), unique=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.activity_id"))
    activity_option_id: Mapped[int] = mapped_column(ForeignKey("activity_options.activity_option_id"))

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=sql.func.now())

    activity: Mapped["Activity"] = relationship("Activity")
    activity_option: Mapped["ActivityOption"] = relationship("ActivityOption")
    character: Mapped["Character"] = relationship("Character")

    def __str__(self) -> str:
        return f"""{self.activity.activity_name}\n            \tStart Time: {self.started_at} ({pendulum.instance(self.started_at).diff_for_humans()})\
        """


class Character(TimestampMixin, Base):
    """Represents a player character in the game.

    A character can perform activities, gain experience in skills,
    and collect items in their inventory.

    Attributes:
        character_id (int): Unique identifier for the character
        character_name (str): Unique name of the character
        skills (list[CharacterSkill]): Character's skills and experience levels
        activities (list[CharacterActivity]): Current and past activities
        items (list[CharacterItem]): Items in the character's inventory

    Relationships:
        skills: One-to-many relationship to CharacterSkill
        activities: One-to-many relationship to CharacterActivity
        items: One-to-many relationship to CharacterItem
    """

    __tablename__ = "characters"

    character_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_name: Mapped[str] = mapped_column(unique=True)

    skills: Mapped[list["CharacterSkill"]] = relationship("CharacterSkill", uselist=True)
    items: Mapped[list["CharacterItem"]] = relationship("CharacterItem", uselist=True, overlaps="character")
    current_activity: Mapped[CharacterActivity] = relationship("CharacterActivity", overlaps="character")
    activity_history: Mapped[list["CharacterActivityHistory"]] = relationship("CharacterActivityHistory", uselist=True)


class CharacterSkill(TimestampMixin, Base):
    """Represents a character's skill level and experience in an activity.

    Each character can have multiple skills, corresponding to different activities.
    Experience points determine the level in each skill.

    Attributes:
        character_skill_id (int): Unique identifier for this skill record
        character_id (int): Foreign key to the Character
        activity_id (int): Foreign key to the Activity this skill relates to
        experience (int): Total experience points earned in this skill

    Relationships:
        character: Many-to-one relationship to Character

    Properties:
        level (int): The current level based on experience points
    """

    __tablename__ = "character_skills"

    character_skill_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.character_id"))
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.activity_id"))
    experience: Mapped[int] = mapped_column(default=0)

    character: Mapped["Character"] = relationship("Character", overlaps="skills")
    skill: Mapped[int] = relationship("Activity")

    @property
    def level(self) -> int:
        """Calculate the current level based on total experience points.

        Returns:
            int: The current level in this skill
        """
        return xp_to_level(self.experience)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure a datetime is timezone-aware in UTC.

    Args:
        dt (Optional[datetime]): The datetime to convert, or None

    Returns:
        Optional[datetime]: The datetime in UTC if provided, None if input was None

    Examples:
        >>> ensure_utc(datetime(2025, 1, 1))  # naive datetime
        DateTime(2025, 1, 1, 0, 0, 0, tzinfo=+00:00)
        >>> ensure_utc(None)
        None
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return pendulum.instance(dt, tz="UTC")
    return dt


class CharacterActivityHistory(TimestampMixin, Base):
    __tablename__ = "character_activity_history"

    character_activity_history_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.character_id"))
    activity_option_id: Mapped[int] = mapped_column(ForeignKey("activity_options.activity_option_id"))
    started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))

    activity_option: Mapped[ActivityOption] = relationship("ActivityOption")

    item_rewards: Mapped[list["CharacterActivityItemReward"]] = relationship(
        "CharacterActivityItemReward", uselist=True
    )
    experience_rewards: Mapped[list["CharacterActivityExperienceReward"]] = relationship(
        "CharacterActivityExperienceReward", uselist=True
    )
    item_costs: Mapped[list["CharacterActivityItemCost"]] = relationship("CharacterActivityItemCost", uselist=True)
    experience_rewards: Mapped[list["CharacterActivityExperienceReward"]] = relationship(
        "CharacterActivityExperienceReward", uselist=True
    )


class CharacterActivityItemReward(TimestampMixin, Base):
    __tablename__ = "character_activity_item_rewards"

    character_activity_item_reward_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_activity_history_id: Mapped[int] = mapped_column(
        ForeignKey("character_activity_history.character_activity_history_id")
    )
    item_id: Mapped[int] = mapped_column(ForeignKey("items.item_id"))
    quantity: Mapped[int] = mapped_column(CheckConstraint("quantity > 0"))


class CharacterActivityExperienceReward(TimestampMixin, Base):
    __tablename__ = "character_activity_experience_rewards"

    character_activity_experience_reward_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_activity_history_id: Mapped[int] = mapped_column(
        ForeignKey("character_activity_history.character_activity_history_id")
    )
    skill_id: Mapped[int] = mapped_column(ForeignKey("activities.activity_id"))
    experience: Mapped[int] = mapped_column(CheckConstraint("experience > 0"))


class CharacterActivityItemCost(TimestampMixin, Base):
    __tablename__ = "character_activity_item_costs"

    character_activity_item_cost_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    character_activity_history_id: Mapped[int] = mapped_column(
        ForeignKey("character_activity_history.character_activity_history_id")
    )
    item_id: Mapped[int] = mapped_column(ForeignKey("items.item_id"))
    quantity: Mapped[int] = mapped_column(CheckConstraint("quantity > 0"))
