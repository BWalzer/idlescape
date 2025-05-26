from dataclasses import dataclass
from typing import Optional

import pendulum
import sqlalchemy.orm

from idlescape.character import Activity, Character, CharacterActivity, CharacterItem, CharacterSkill, Item


@dataclass
class ItemData:
    item_id: int
    item_name: str

    created_at: pendulum.DateTime
    updated_at: pendulum.DateTime


@dataclass
class CharacterItemData:
    character_item_id: int
    character_id: int
    item_id: int
    item: ItemData


@dataclass
class ActivityData:
    activity_id: int
    activity_name: str
    activity_type: str


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
        return f"{self.activity.activity_name.title()}: {self.experience}xp"


@dataclass
class CharacterActivityData:
    character_activity_id: int
    activity_id: int
    character_id: int
    activity: ActivityData
    started_at: pendulum.DateTime
    ended_at: Optional[pendulum.DateTime]


@dataclass
class CharacterData:
    character_id: int
    character_name: str
    current_activity: Optional[CharacterActivityData]
    skills: list[CharacterSkillData]
    created_at: pendulum.DateTime

    def __str__(self) -> str:
        # TODO: Make this prettier, colors, bold, etc.
        current_activity_str = (
            f"{self.current_activity.activity.activity_name.title()}, started {self.current_activity.started_at.diff_for_humans()}"
            if self.current_activity
            else "None"
        )
        return f"""\
            Name: {self.character_name}
            Created: {self.created_at} - {self.created_at.diff_for_humans()}
            Current Activity: {current_activity_str}
            Skills:
                {"\n\t\t".join([str(skill) for skill in self.skills])}\
        """


def character_to_data(character: Character, session: sqlalchemy.orm.Session) -> CharacterData:
    current_activity = (
        session.query(CharacterActivity).filter_by(character_id=character.character_id, ended_at=None).one_or_none()
    )

    return CharacterData(
        character_id=character.character_id,
        character_name=character.character_name,
        current_activity=character_activity_to_data(current_activity, session) if current_activity else None,
        skills=[character_skill_to_data(skill, session) for skill in character.skills],
        created_at=pendulum.instance(character.created_at, tz="utc"),
    )


def activity_to_data(activity: Activity) -> ActivityData:
    return ActivityData(
        activity_id=activity.activity_id, activity_name=activity.activity_name, activity_type=activity.activity_type
    )


def character_activity_to_data(
    character_activity: CharacterActivity,
    session: sqlalchemy.orm.Session,
) -> CharacterActivityData:
    activity = session.query(Activity).filter_by(activity_id=character_activity.activity_id).one()
    return CharacterActivityData(
        character_activity_id=character_activity.character_activity_id,
        activity_id=character_activity.activity_id,
        activity=activity_to_data(activity),
        character_id=character_activity.character_id,
        started_at=pendulum.instance(character_activity.started_at, tz="utc"),
        ended_at=pendulum.instance(character_activity.ended_at, tz="utc") if character_activity.ended_at else None,
    )


def character_skill_to_data(character_skill: CharacterSkill, session: sqlalchemy.orm.Session) -> CharacterSkillData:
    activity = session.query(Activity).filter_by(activity_id=character_skill.activity_id).one()

    return CharacterSkillData(
        character_skill_id=character_skill.character_skill_id,
        character_id=character_skill.character_id,
        activity_id=character_skill.activity_id,
        experience=character_skill.experience,
        activity=activity_to_data(activity),
        created_at=character_skill.created_at,
        updated_at=character_skill.updated_at,
    )


def item_to_data(item: Item, session: sqlalchemy.orm.Session) -> ItemData:
    return ItemData(item_id=item.item_id, item_name=item.item_name)


def character_item_to_data(character_item: CharacterItem, session: sqlalchemy.orm.Session) -> CharacterItemData:
    item = session.query(Item).filter_by(item_id=character_item.item_id).one()
    return CharacterItemData(
        character_item_id=character_item.character_item_id,
        character_id=character_item.character_id,
        item_id=character_item.item_id,
        item=item_to_data(item, session),
        created_at=pendulum.instance(character_item.created_at, tz="utc"),
        updated_at=pendulum.instance(character_item.updated_at, tz="utc"),
    )
