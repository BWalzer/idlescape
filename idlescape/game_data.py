from dataclasses import dataclass
from typing import Optional, Self

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
    item_id: int
    item_name: str

    created_at: pendulum.DateTime
    updated_at: pendulum.DateTime

    @classmethod
    def from_orm(cls, item: Item, session: sqlalchemy.orm.Session) -> "ItemData":
        return cls(
            item_id=item.item_id,
            item_name=item.item_name,
            created_at=pendulum.instance(item.created_at, tz="utc"),
            updated_at=pendulum.instance(item.updated_at, tz="utc"),
        )


@dataclass
class CharacterItemData:
    character_item_id: int
    character_id: int
    item_id: int
    item: ItemData
    quantity: int

    created_at: pendulum.DateTime
    updated_at: pendulum.DateTime

    @classmethod
    def from_orm(cls, character_item: CharacterItem, session: sqlalchemy.orm.Session) -> "CharacterItemData":
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
        return f"{self.item.item_name.title()}: {self.quantity:,}"


@dataclass
class ActivityData:
    activity_id: int
    activity_name: str
    activity_type: str

    @classmethod
    def from_orm(cls, activity: Activity) -> "ActivityData":
        return cls(
            activity_id=activity.activity_id,
            activity_name=activity.activity_name,
            activity_type=activity.activity_type,
        )


@dataclass
class ActivityOptionData:
    activity_option_id: int
    activity_option_name: str
    activity_id: int
    action_time: int
    reward_item_id: int
    reward_experience: int
    skill_requirements: dict

    @classmethod
    def from_orm(cls, activity_option: ActivityOption) -> "ActivityOptionData":
        return cls(
            activity_option_id=activity_option.activity_option_id,
            activity_option_name=activity_option.activity_option_name,
            activity_id=activity_option.activity_id,
            action_time=activity_option.action_time,
            reward_item_id=activity_option.reward_item_id,
            reward_experience=activity_option.reward_experience,
            skill_requirements=activity_option.skill_requirements,
        )


@dataclass
class CharacterSkillData:
    character_skill_id: int
    character_id: int
    activity_id: int
    experience: int
    activity: ActivityData
    created_at: pendulum.DateTime
    updated_at: pendulum.DateTime

    def __str__(self) -> str:
        return f"{self.activity.activity_name.title()}: Lvl {self.level} - {self.experience:,}xp"

    @property
    def level(self) -> int:
        return xp_to_level(self.experience)

    @classmethod
    def from_orm(cls, character_skill: CharacterSkill, session: sqlalchemy.orm.Session) -> "CharacterSkillData":
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
    character_id: int
    character_name: str
    current_activity: Optional[CharacterActivityData]
    skills: list[CharacterSkillData]
    items: list[CharacterItemData]
    created_at: pendulum.DateTime

    def __str__(self) -> str:
        # TODO: Make this prettier, colors, bold, etc.
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
