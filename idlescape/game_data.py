from dataclasses import dataclass
from typing import Optional

import pendulum
import sqlalchemy.orm

from idlescape.character import (
    Activity,
    ActivityOption,
    ActivityOptionItemCost,
    ActivityOptionSkillRequirement,
    Character,
    CharacterActivity,
    CharacterActivityExperienceReward,
    CharacterActivityHistory,
    CharacterActivityItemCost,
    CharacterActivityItemReward,
    CharacterItem,
    CharacterSkill,
    Item,
    ensure_utc,
)
from idlescape.experience_to_level import xp_to_level


@dataclass
class TimestampMixinDTO:
    created_at: pendulum.DateTime
    updated_at: pendulum.DateTime

    def __post_init__(self):
        self.created_at = pendulum.instance(self.created_at, tz="utc")
        self.updated_at = pendulum.instance(self.updated_at, tz="utc")


@dataclass
class ActivityOptionItemCostData:
    activity_option_item_cost_id: int
    activity_option_id: int
    item_id: int
    quantity: int

    @classmethod
    def from_orm(cls, item_cost: ActivityOptionItemCost) -> "ActivityOptionItemCostData":
        """Convert an ActivityOptionItemCost ORM model to ActivityOptionItemCostData.

        Args:
            item_cost (ActivityOptionItemCost): The ORM model to convert

        Returns:
            ActivityOptionItemCostData: A data transfer object representing the item cost
        """
        return cls(
            activity_option_item_cost_id=item_cost.activity_option_item_cost_id,
            activity_option_id=item_cost.activity_option_id,
            item_id=item_cost.item_id,
            quantity=item_cost.quantity,
        )


@dataclass
class ActivityOptionSkillRequirementData:
    activity_option_skill_requirement_id: int
    activity_option_id: int
    skill_id: int
    required_level: int

    @classmethod
    def from_orm(cls, skill_requirement: ActivityOptionSkillRequirement) -> "ActivityOptionSkillRequirementData":
        """Convert an ActivityOptionSkillRequirement ORM model to ActivityOptionSkillRequirementData.

        Args:
            skill_requirement (ActivityOptionSkillRequirement): The ORM model to convert

        Returns:
            ActivityOptionSkillRequirementData: A data transfer object representing the skill requirement
        """
        return cls(
            activity_option_skill_requirement_id=skill_requirement.activity_option_skill_requirement_id,
            activity_option_id=skill_requirement.activity_option_id,
            skill_id=skill_requirement.skill_id,
            required_level=skill_requirement.required_level,
        )


@dataclass
class ItemData(TimestampMixinDTO):
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

    @classmethod
    def from_orm(cls, item: Item) -> "ItemData":
        """Convert an Item ORM model to ItemData.

        Args:
            item (Item): The Item ORM model to convert

        Returns:
            ItemData: A data transfer object representing the item
        """
        return cls(
            item_id=item.item_id,
            item_name=item.item_name,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )


@dataclass
class CharacterItemData(TimestampMixinDTO):
    """Data transfer object for CharacterItem ORM model.

    This class represents an item in a character's inventory,
    including the item's details and quantity owned.

    Attributes:
        character_item_id (int): Unique identifier for this inventory entry
        character_id (int): ID of the owning character
        item_id (int): ID of the item
        item (ItemData): Details of the item
        quantity (int): Number of this item owned
    """

    character_item_id: int
    character_id: int
    item_id: int
    quantity: int
    character: "CharacterData"
    item: ItemData

    @classmethod
    def from_orm(cls, character_item: CharacterItem) -> "CharacterItemData":
        """Convert a CharacterItem ORM model to CharacterItemData.

        Args:
            character_item (CharacterItem): The CharacterItem ORM model to convert

        Returns:
            CharacterItemData: A data transfer object representing the inventory item
        """
        return cls(
            character_item_id=character_item.character_item_id,
            character_id=character_item.character_id,
            item_id=character_item.item_id,
            quantity=character_item.quantity,
            character=character_item.character,
            item=ItemData.from_orm(character_item.item),
            created_at=character_item.created_at,
            updated_at=character_item.updated_at,
        )

    def __str__(self) -> str:
        """Format the inventory item for display.

        Returns:
            str: A string representation showing the item name and quantity
        """
        return f"{self.item.item_name.title()}: {self.quantity:,}"


@dataclass
class ActivityData(TimestampMixinDTO):
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
            created_at=activity.created_at,
            updated_at=activity.updated_at,
        )


@dataclass
class ActivityOptionData(TimestampMixinDTO):
    """Data transfer object for ActivityOption ORM model.

    This class represents a specific action that can be performed within an activity,
    such as mining iron ore within the mining activity.

    Attributes:
        activity_option_id (int): Unique identifier for this option
        activity_option_name (str): Name of the specific action (e.g., "iron")
        activity_id (int): ID of the parent activity
        action_time (int): Time in seconds this action takes to complete
    """

    activity_option_id: int
    activity_option_name: str
    activity_id: int
    action_time: int
    activity: ActivityData

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
            activity=ActivityData.from_orm(activity_option.activity),
            created_at=activity_option.created_at,
            updated_at=activity_option.updated_at,
        )


@dataclass
class CharacterSkillData(TimestampMixinDTO):
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
    skill: ActivityData

    def __str__(self) -> str:
        """Format the skill for display.

        Returns:
            str: A string showing the skill name, level, and experience
        """
        return f"{self.skill.activity_name.title()}: Lvl {self.level} - {self.experience:,}xp"

    @property
    def level(self) -> int:
        """Calculate the current level based on total experience points.

        Returns:
            int: The current level in this skill
        """
        return xp_to_level(self.experience)

    @classmethod
    def from_orm(cls, character_skill: CharacterSkill) -> "CharacterSkillData":
        """Convert a CharacterSkill ORM model to CharacterSkillData.

        Args:
            character_skill (CharacterSkill): The CharacterSkill ORM model to convert

        Returns:
            CharacterSkillData: A data transfer object representing the skill
        """
        return cls(
            character_skill_id=character_skill.character_skill_id,
            character_id=character_skill.character_id,
            activity_id=character_skill.activity_id,
            experience=character_skill.experience,
            skill=ActivityData.from_orm(character_skill.skill),
            created_at=character_skill.created_at,
            updated_at=character_skill.updated_at,
        )


@dataclass
class CharacterActivityData(TimestampMixinDTO):
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
    """

    character_activity_id: int
    activity_id: int
    character_id: int
    activity_option_id: int
    started_at: pendulum.DateTime
    activity: ActivityData
    activity_option: ActivityOptionData

    @classmethod
    def from_orm(cls, character_activity: CharacterActivity) -> "CharacterActivityData":
        """Convert a CharacterActivity ORM model to CharacterActivityData.

        Args:
            character_activity (CharacterActivity): The CharacterActivity ORM model to convert

        Returns:
            CharacterActivityData: A data transfer object representing the activity
        """
        return cls(
            character_activity_id=character_activity.character_activity_id,
            character_id=character_activity.character_id,
            activity_id=character_activity.activity_id,
            activity_option_id=character_activity.activity_option_id,
            started_at=ensure_utc(character_activity.started_at),
            activity=ActivityData.from_orm(character_activity.activity),
            activity_option=ActivityOptionData.from_orm(character_activity.activity_option),
            created_at=character_activity.created_at,
            updated_at=character_activity.updated_at,
        )


@dataclass
class CharacterData(TimestampMixinDTO):
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
    activity_history: list["CharacterActivityHistoryData"]
    skills: list[CharacterSkillData]
    items: list[CharacterItemData]

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
            Activity History:
                {"\n\t\t".join([str(activity) for activity in self.activity_history])}
        """

    @classmethod
    def from_orm(cls, character: Character) -> "CharacterData":
        """Convert a Character ORM model to CharacterData.

        Args:
            character (Character): The Character ORM model to convert

        Returns:
            CharacterData: A data transfer object representing the character
        """
        return cls(
            character_id=character.character_id,
            character_name=character.character_name,
            current_activity=CharacterActivityData.from_orm(character.current_activity)
            if character.current_activity
            else None,
            activity_history=[
                CharacterActivityHistoryData.from_orm(activity) for activity in character.activity_history
            ],
            skills=[CharacterSkillData.from_orm(skill) for skill in character.skills],
            items=[CharacterItemData.from_orm(item) for item in character.items],
            created_at=character.created_at,
            updated_at=character.updated_at,
        )


@dataclass
class CharacterActivityItemRewardData(TimestampMixinDTO):
    character_activity_item_reward_id: int
    character_activity_history_id: int
    item_id: int
    quantity: int

    @classmethod
    def from_orm(cls, character_activity_item_reward: CharacterActivityItemReward) -> "CharacterActivityItemReward":
        return cls(
            character_activity_item_reward_id=character_activity_item_reward.character_activity_item_reward_id,
            character_activity_history_id=character_activity_item_reward.character_activity_history_id,
            item_id=character_activity_item_reward.item_id,
            quantity=character_activity_item_reward.quantity,
            created_at=character_activity_item_reward.created_at,
            updated_at=character_activity_item_reward.updated_at,
        )


@dataclass
class CharacterActivityExperienceRewardData(TimestampMixinDTO):
    character_activity_experience_reward_id: int
    character_activity_history_id: int
    skill_id: int
    reward_experience: int

    @classmethod
    def from_orm(
        cls, character_activity_experience_reward: CharacterActivityExperienceReward
    ) -> "CharacterActivityExperienceRewardData":
        return cls(
            character_activity_experience_reward_id=character_activity_experience_reward.character_activity_experience_reward_id,
            character_activity_history_id=character_activity_experience_reward.character_activity_history_id,
            skill_id=character_activity_experience_reward.skill_id,
            reward_experience=character_activity_experience_reward.experience,
            created_at=character_activity_experience_reward.created_at,
            updated_at=character_activity_experience_reward.updated_at,
        )


@dataclass
class CharacterActivityItemCostData(TimestampMixinDTO):
    character_activity_item_cost_id: int
    character_activity_history_id: int
    item_id: int
    quantity: int

    @classmethod
    def from_orm(cls, character_activity_item_cost: CharacterActivityItemCost) -> "CharacterActivityItemCostData":
        return cls(
            character_activity_item_cost_id=character_activity_item_cost.character_activity_item_cost_id,
            character_activity_history_id=character_activity_item_cost.character_activity_history_id,
            item_id=character_activity_item_cost.item_id,
            quantity=character_activity_item_cost.quantity,
            created_at=character_activity_item_cost.created_at,
            updated_at=character_activity_item_cost.updated_at,
        )


@dataclass
class CharacterActivityHistoryData(TimestampMixinDTO):
    character_activity_history_id: int
    character_id: int
    activity_option_id: int
    started_at: pendulum.DateTime
    ended_at: pendulum.DateTime
    activity_option: ActivityOptionData

    item_rewards: list[CharacterActivityItemRewardData]
    experience_rewards: list[CharacterActivityExperienceRewardData]
    item_costs: list[CharacterActivityItemCostData]

    @classmethod
    def from_orm(cls, character_activity_history: CharacterActivityHistory) -> "CharacterActivityHistoryData":
        return cls(
            character_activity_history_id=character_activity_history.character_activity_history_id,
            character_id=character_activity_history.character_id,
            activity_option_id=character_activity_history.activity_option_id,
            started_at=pendulum.instance(character_activity_history.started_at, tz="utc"),
            ended_at=pendulum.instance(character_activity_history.ended_at, tz="utc"),
            activity_option=ActivityOptionData.from_orm(character_activity_history.activity_option),
            item_rewards=[
                CharacterActivityItemRewardData.from_orm(item_reward)
                for item_reward in character_activity_history.item_rewards
            ],
            experience_rewards=[
                CharacterActivityExperienceRewardData.from_orm(xp_reward)
                for xp_reward in character_activity_history.experience_rewards
            ],
            item_costs=[
                CharacterActivityItemCostData.from_orm(item_cost) for item_cost in character_activity_history.item_costs
            ],
            created_at=character_activity_history.created_at,
            updated_at=character_activity_history.updated_at,
        )

    def __str__(self) -> str:
        return f"{self.activity_option.activity.activity_name.title()} - {self.activity_option.activity_option_name}: Started - {self.started_at}, Ended - {self.ended_at}, Duration: {self.started_at.diff_for_humans(self.ended_at, absolute=True)}"
