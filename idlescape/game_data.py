from dataclasses import dataclass
from typing import Optional

import pendulum
import sqlalchemy.orm

from idlescape.character import (
    Activity,
    ActivityOption,
    Character,
    CharacterActivity,
    CharacterItem,
    CharacterSkill,
    Item,
)
from idlescape.experience_to_level import xp_to_level


@dataclass
class ItemData:
    """Data transfer object for Item ORM model.

    This class provides a plain data representation of an Item,
    suitable for serialization and API responses.

    Attributes:
        item_id (int): Unique identifier for the item
        item_name (str): Unique name of the item
        created_at (pendulum.DateTime): UTC timestamp when the item was created
        updated_at (pendulum.DateTime): UTC timestamp when the item was last updated
    """

    item_id: int
    item_name: str

    created_at: pendulum.DateTime
    updated_at: pendulum.DateTime

    @classmethod
    def from_orm(cls, item: Item, session: sqlalchemy.orm.Session) -> "ItemData":
        """Convert an Item ORM model to ItemData.

        Args:
            item (Item): The Item ORM model to convert
            session (sqlalchemy.orm.Session): The database session

        Returns:
            ItemData: A data transfer object representing the item
        """
        return cls(
            item_id=item.item_id,
            item_name=item.item_name,
            created_at=pendulum.instance(item.created_at, tz="utc"),
            updated_at=pendulum.instance(item.updated_at, tz="utc"),
        )


@dataclass
class CharacterItemData:
    """Data transfer object for CharacterItem ORM model.

    This class represents an item in a character's inventory,
    including the item's details and quantity owned.

    Attributes:
        character_item_id (int): Unique identifier for this inventory entry
        character_id (int): ID of the owning character
        item_id (int): ID of the item
        item (ItemData): Details of the item
        quantity (int): Number of this item owned
        created_at (pendulum.DateTime): UTC timestamp when the entry was created
        updated_at (pendulum.DateTime): UTC timestamp when last updated
    """

    character_item_id: int
    character_id: int
    item_id: int
    item: ItemData
    quantity: int

    created_at: pendulum.DateTime
    updated_at: pendulum.DateTime

    @classmethod
    def from_orm(cls, character_item: CharacterItem, session: sqlalchemy.orm.Session) -> "CharacterItemData":
        """Convert a CharacterItem ORM model to CharacterItemData.

        Args:
            character_item (CharacterItem): The CharacterItem ORM model to convert
            session (sqlalchemy.orm.Session): The database session

        Returns:
            CharacterItemData: A data transfer object representing the inventory item
        """
        item = session.query(Item).filter_by(item_id=character_item.item_id).one()
        return cls(
            character_item_id=character_item.character_item_id,
            character_id=character_item.character_id,
            item_id=character_item.item_id,
            item=ItemData.from_orm(item, session),
            quantity=character_item.quantity,
            created_at=pendulum.instance(character_item.created_at, tz="utc"),
            updated_at=pendulum.instance(character_item.updated_at, tz="utc"),
        )

    def __str__(self) -> str:
        """Format the inventory item for display.

        Returns:
            str: A string representation showing the item name and quantity
        """
        return f"{self.item.item_name.title()}: {self.quantity:,}"


@dataclass
class ActivityData:
    """Data transfer object for Activity ORM model.

    This class represents a type of activity that can be performed,
    such as mining or woodcutting.

    Attributes:
        activity_id (int): Unique identifier for the activity
        activity_name (str): Name of the activity (e.g., "mining")
        activity_type (str): Type of activity (affects game mechanics)
    """

    activity_id: int
    activity_name: str
    activity_type: str

    @classmethod
    def from_orm(cls, activity: Activity) -> "ActivityData":
        """Convert an Activity ORM model to ActivityData.

        Args:
            activity (Activity): The Activity ORM model to convert

        Returns:
            ActivityData: A data transfer object representing the activity
        """
        return cls(
            activity_id=activity.activity_id,
            activity_name=activity.activity_name,
            activity_type=activity.activity_type,
        )


@dataclass
class ActivityOptionData:
    """Data transfer object for ActivityOption ORM model.

    This class represents a specific action that can be performed within an activity,
    such as mining iron ore within the mining activity.

    Attributes:
        activity_option_id (int): Unique identifier for this option
        activity_option_name (str): Name of the specific action (e.g., "iron")
        activity_id (int): ID of the parent activity
        action_time (int): Time in seconds this action takes to complete
        reward_item_id (int): ID of the item received as a reward
        reward_experience (int): Experience points granted upon completion
        skill_requirements (dict): Dictionary mapping skill names to required levels
        item_costs(list): List of dictionaries containing items consumed for each action and quantity.
        item_requirements(list): List of dictionaries containing items required, but not consumed.
    """

    activity_option_id: int
    activity_option_name: str
    activity_id: int
    action_time: int
    reward_item_id: int
    reward_experience: int
    skill_requirements: Optional[dict[str, int]]
    item_costs: Optional[list[dict[str, int]]]
    item_requirements: Optional[list[dict[str, int]]]

    @classmethod
    def from_orm(cls, activity_option: ActivityOption) -> "ActivityOptionData":
        """Convert an ActivityOption ORM model to ActivityOptionData.

        Args:
            activity_option (ActivityOption): The ActivityOption ORM model to convert

        Returns:
            ActivityOptionData: A data transfer object representing the activity option
        """
        return cls(
            activity_option_id=activity_option.activity_option_id,
            activity_option_name=activity_option.activity_option_name,
            activity_id=activity_option.activity_id,
            action_time=activity_option.action_time,
            reward_item_id=activity_option.reward_item_id,
            reward_experience=activity_option.reward_experience,
            skill_requirements=activity_option.skill_requirements,
            item_costs=activity_option.item_costs,
            item_requirements=activity_option.item_requirements,
        )


@dataclass
class CharacterSkillData:
    """Data transfer object for CharacterSkill ORM model.

    This class represents a character's progress in a particular skill,
    including experience points and calculated level.

    Attributes:
        character_skill_id (int): Unique identifier for this skill record
        character_id (int): ID of the character
        activity_id (int): ID of the related activity
        experience (int): Total experience points in this skill
        activity (ActivityData): Details of the related activity
        created_at (pendulum.DateTime): UTC timestamp when the skill was first gained
        updated_at (pendulum.DateTime): UTC timestamp when last updated

    Properties:
        level (int): Current level based on experience points
    """

    character_skill_id: int
    character_id: int
    activity_id: int
    experience: int
    activity: ActivityData
    created_at: pendulum.DateTime
    updated_at: pendulum.DateTime

    def __str__(self) -> str:
        """Format the skill for display.

        Returns:
            str: A string showing the skill name, level, and experience
        """
        return f"{self.activity.activity_name.title()}: Lvl {self.level} - {self.experience:,}xp"

    @property
    def level(self) -> int:
        """Calculate the current level based on total experience points.

        Returns:
            int: The current level in this skill
        """
        return xp_to_level(self.experience)

    @classmethod
    def from_orm(cls, character_skill: CharacterSkill, session: sqlalchemy.orm.Session) -> "CharacterSkillData":
        """Convert a CharacterSkill ORM model to CharacterSkillData.

        Args:
            character_skill (CharacterSkill): The CharacterSkill ORM model to convert
            session (sqlalchemy.orm.Session): The database session

        Returns:
            CharacterSkillData: A data transfer object representing the skill
        """
        activity = session.query(Activity).filter_by(activity_id=character_skill.activity_id).one()
        return cls(
            character_skill_id=character_skill.character_skill_id,
            character_id=character_skill.character_id,
            activity_id=character_skill.activity_id,
            experience=character_skill.experience,
            activity=ActivityData.from_orm(activity),
            created_at=character_skill.created_at,
            updated_at=character_skill.updated_at,
        )


@dataclass
class CharacterActivityData:
    """Data transfer object for CharacterActivity ORM model.

    This class represents a character's current or past activity,
    including what they're doing and when they started/finished.

    Attributes:
        character_activity_id (int): Unique identifier for this activity record
        activity_id (int): ID of the activity being performed
        character_id (int): ID of the character performing the activity
        activity_option_id (int): ID of the specific action being performed
        activity (ActivityData): Details of the activity being performed
        activity_option (ActivityOptionData): Details of the specific action
        started_at (pendulum.DateTime): UTC timestamp when the activity was started
        ended_at (Optional[pendulum.DateTime]): UTC timestamp when completed, or None if ongoing
    """

    character_activity_id: int
    activity_id: int
    character_id: int
    activity_option_id: int
    activity: ActivityData
    activity_option: ActivityOptionData
    started_at: pendulum.DateTime
    ended_at: Optional[pendulum.DateTime]

    @classmethod
    def from_orm(
        cls,
        character_activity: CharacterActivity,
        session: sqlalchemy.orm.Session,
    ) -> "CharacterActivityData":
        """Convert a CharacterActivity ORM model to CharacterActivityData.

        Args:
            character_activity (CharacterActivity): The CharacterActivity ORM model to convert
            session (sqlalchemy.orm.Session): The database session

        Returns:
            CharacterActivityData: A data transfer object representing the activity
        """
        activity = session.query(Activity).filter_by(activity_id=character_activity.activity_id).one()
        activity_option = (
            session.query(ActivityOption).filter_by(activity_option_id=character_activity.activity_option_id).one()
        )
        return cls(
            character_activity_id=character_activity.character_activity_id,
            activity_id=character_activity.activity_id,
            activity=ActivityData.from_orm(activity),
            activity_option_id=character_activity.activity_option_id,
            activity_option=ActivityOptionData.from_orm(activity_option),
            character_id=character_activity.character_id,
            started_at=pendulum.instance(character_activity.started_at, tz="utc"),
            ended_at=pendulum.instance(character_activity.ended_at, tz="utc") if character_activity.ended_at else None,
        )


@dataclass
class CharacterData:
    """Data transfer object for Character ORM model.

    This class provides a complete view of a character's state,
    including their current activity, skills, and inventory.

    Attributes:
        character_id (int): Unique identifier for the character
        character_name (str): Name of the character
        current_activity (Optional[CharacterActivityData]): Current activity if any
        skills (list[CharacterSkillData]): List of character's skills
        items (list[CharacterItemData]): List of items in inventory
        created_at (pendulum.DateTime): UTC timestamp when character was created
    """

    character_id: int
    character_name: str
    current_activity: Optional[CharacterActivityData]
    skills: list[CharacterSkillData]
    items: list[CharacterItemData]
    created_at: pendulum.DateTime

    def __str__(self) -> str:
        """Format the character's information for display.

        Creates a multi-line string showing the character's name, creation date,
        current activity, skills, and inventory.

        Returns:
            str: A formatted string representation of the character
        """
        current_activity_str = (
            f"{self.current_activity.activity.activity_name.title()} - {self.current_activity.activity_option.activity_option_name}, started {self.current_activity.started_at.diff_for_humans()}"
            if self.current_activity
            else "None"
        )
        return f"""\
            Name: {self.character_name}
            Created: {self.created_at} - {self.created_at.diff_for_humans()}
            Current Activity: {current_activity_str}
            Skills:
                {"\n\t\t".join([str(skill) for skill in self.skills])}
            Items:
                {"\n\t\t".join([str(item) for item in self.items])}
        """

    @classmethod
    def from_orm(cls, character: Character, session: sqlalchemy.orm.Session) -> "CharacterData":
        """Convert a Character ORM model to CharacterData.

        Args:
            character (Character): The Character ORM model to convert
            session (sqlalchemy.orm.Session): The database session

        Returns:
            CharacterData: A data transfer object representing the character
        """
        current_activity = (
            session.query(CharacterActivity).filter_by(character_id=character.character_id, ended_at=None).one_or_none()
        )
        items = [CharacterItemData.from_orm(item, session) for item in character.items]
        return cls(
            character_id=character.character_id,
            character_name=character.character_name,
            current_activity=CharacterActivityData.from_orm(current_activity, session) if current_activity else None,
            skills=[CharacterSkillData.from_orm(skill, session) for skill in character.skills],
            items=items,
            created_at=pendulum.instance(character.created_at, tz="utc"),
        )
