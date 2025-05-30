import functools
import importlib.resources
import json
from typing import Optional

import pendulum
import sqlalchemy
import sqlalchemy.orm

from idlescape.character import (
    Activity,
    Base,
    Character,
    CharacterActivity,
    CharacterActivityExperienceReward,
    CharacterActivityHistory,
    CharacterActivityItemCost,
    CharacterActivityItemReward,
    CharacterSkill,
    ensure_utc,
)
from idlescape.game_data import (
    ActivityData,
    ActivityOption,
    ActivityOptionData,
    CharacterActivityData,
    CharacterData,
    CharacterItem,
    CharacterItemData,
    CharacterSkillData,
    Item,
)


def with_session(func):
    """
    Decorator to provide a SQLAlchemy session to a function and handle commit/rollback.
    Args:
        func: The function to wrap. Must accept a 'session' keyword argument.
    Returns:
        The wrapped function with session management.
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        with sqlalchemy.orm.Session(self.engine) as session:
            try:
                result = func(self, *args, session=session, **kwargs)
                session.commit()
                return result
            except Exception:
                session.rollback()
                raise

    return wrapper


class Game:
    """
    Main game logic class for Idlescape.
    Handles character creation, activities, skills, items, and database management.
    """

    def __init__(self, db_filepath: str = "sqlite:///idlescape.db"):
        """
        Initialize the Game instance and create/load the database schema and static data.
        Args:
            db_filepath: Path to the SQLite database file.
        """
        self.engine = sqlalchemy.create_engine(db_filepath)
        Base.metadata.create_all(self.engine)
        with sqlalchemy.orm.Session(self.engine) as session:
            self._load_activities(session)
            self._load_items(session)
            self._load_activity_options(session)
            self._load_skill_requirements(session)
            self._load_item_costs(session)
            self._load_item_rewards(session)
            self._load_experience_rewards(session)
            session.commit()

    def _load_item_rewards(self, session: sqlalchemy.orm.Session) -> None:
        from idlescape.character import ActivityOptionItemReward

        session.query(ActivityOptionItemReward).delete()
        with importlib.resources.open_text("idlescape.data", "activity_option_item_rewards.json") as f:
            item_rewards: list[dict[str, int]] = json.load(f)
        session.add_all([ActivityOptionItemReward(**item_reward) for item_reward in item_rewards])

    def _load_experience_rewards(self, session: sqlalchemy.orm.Session) -> None:
        from idlescape.character import ActivityOptionExperienceReward

        session.query(ActivityOptionExperienceReward).delete()
        with importlib.resources.open_text("idlescape.data", "activity_option_experience_rewards.json") as f:
            xp_rewards: list[dict[str, int]] = json.load(f)
        session.add_all([ActivityOptionExperienceReward(**xp_reward) for xp_reward in xp_rewards])

    def _load_skill_requirements(self, session: sqlalchemy.orm.Session) -> None:
        from idlescape.game_data import ActivityOptionSkillRequirement

        session.query(ActivityOptionSkillRequirement).delete()
        with importlib.resources.open_text("idlescape.data", "activity_option_skill_requirements.json") as f:
            skill_requirements: list[dict] = json.load(f)
        session.add_all([ActivityOptionSkillRequirement(**requirement) for requirement in skill_requirements])

    def _load_item_costs(self, session: sqlalchemy.orm.Session) -> None:
        from idlescape.game_data import ActivityOptionItemCost

        session.query(ActivityOptionItemCost).delete()
        with importlib.resources.open_text("idlescape.data", "activity_option_item_costs.json") as f:
            item_costs: list[dict] = json.load(f)
        session.add_all([ActivityOptionItemCost(**cost) for cost in item_costs])

    def _load_activity_options(self, session: sqlalchemy.orm.Session) -> None:
        session.query(ActivityOption).delete()
        with importlib.resources.open_text("idlescape.data", "activity_options.json") as f:
            activity_options: list[dict] = json.load(f)
        session.add_all([ActivityOption(**activity_option) for activity_option in activity_options])

    def _load_items(self, session: sqlalchemy.orm.Session) -> None:
        session.query(Item).delete()
        with importlib.resources.open_text("idlescape.data", "items.json") as f:
            items: list[dict] = json.load(f)
        session.add_all([Item(**item) for item in items])

    def _load_activities(self, session: sqlalchemy.orm.Session) -> None:
        session.query(Activity).delete()
        with importlib.resources.open_text("idlescape.data", "activities.json") as f:
            activities: list[dict] = json.load(f)
        session.add_all([Activity(**activity) for activity in activities])

    def _init_character_skills(self, character_name: str, session: sqlalchemy.orm.Session):
        """
        Initialize all skill records for a new character.
        Args:
            character_name: The name of the character.
            session: SQLAlchemy session.
        """
        char: Character = session.query(Character).filter_by(character_name=character_name).one()
        skills: list[Activity] = session.query(Activity).filter_by(activity_type="skill").all()
        for skill in skills:
            char_skill = (
                session.query(CharacterSkill)
                .filter_by(character_id=char.character_id, activity_id=skill.activity_id)
                .one_or_none()
            )
            if not char_skill:
                new_char_skill = CharacterSkill(character_id=char.character_id, activity_id=skill.activity_id)
                session.add(new_char_skill)

    @with_session
    def create_character(self, character_name: str, session: sqlalchemy.orm.Session) -> CharacterData:
        """
        Create a new character and initialize their skills.
        Args:
            character_name: The name of the new character.
            session: SQLAlchemy session (provided by decorator).
        Returns:
            CharacterData for the new character.
        """
        char = Character(character_name=character_name)
        session.add(char)
        session.flush()  # To get autogenerated fields like character_id
        self._init_character_skills(character_name, session)
        return CharacterData.from_orm(char)

    def _get_character_by_name(self, character_name: str, session: sqlalchemy.orm.Session) -> Character:
        """Get a Character ORM object by name.

        Args:
            character_name: The name of the character.
            session: SQLAlchemy session.

        Returns:
            Character ORM object or None if not found.
        """
        return session.query(Character).filter_by(character_name=character_name).one()

    def _get_character_skill(
        self, character: Character, skill: Activity, session: sqlalchemy.orm.Session
    ) -> CharacterSkill:
        """Get a character's skill ORM object.

        Args:
            character: Character ORM object.
            skill: Activity ORM object representing the skill.
            session: SQLAlchemy session.

        Returns:
            CharacterSkill ORM object.

        Raises:
            sqlalchemy.exc.NoResultFound: If skill not found for character.
        """
        return (
            session.query(CharacterSkill)
            .filter_by(character_id=character.character_id, activity_id=skill.activity_id)
            .one()
        )

    def _get_current_activity(
        self, character: Character, session: sqlalchemy.orm.Session
    ) -> Optional[CharacterActivity]:
        """Get the current activity ORM object for a character.

        Args:
            character_name: The name of the character.
            session: SQLAlchemy session.

        Returns:
            CharacterActivity ORM object or None if no current activity.
        """
        if not character:
            return None
        return session.query(CharacterActivity).filter_by(character_id=character.character_id).one_or_none()

    @with_session
    def get_character_by_name(self, character_name: str, session: sqlalchemy.orm.Session) -> CharacterData:
        """
        Get a character's data by name.
        Args:
            character_name: The name of the character.
            session: SQLAlchemy session (provided by decorator).
        Returns:
            CharacterData or None if not found.
        """
        return CharacterData.from_orm(self._get_character_by_name(character_name, session))

    def _get_activity_by_name(self, activity_name: str, session: sqlalchemy.orm.Session) -> Activity:
        """Get an activity ORM object by name.

        Args:
            activity_name: The name of the activity.
            session: SQLAlchemy session.

        Returns:
            Activity ORM object.

        Raises:
            sqlalchemy.exc.NoResultFound: If activity not found.
        """
        return session.query(Activity).filter_by(activity_name=activity_name).one()

    @with_session
    def get_activity_by_name(self, activity_name: str, session: sqlalchemy.orm.Session) -> ActivityData:
        """Get an activity's data by name.

        Args:
            activity_name: The name of the activity.
            session: SQLAlchemy session (provided by decorator).

        Returns:
            ActivityData for the activity.

        Raises:
            sqlalchemy.exc.NoResultFound: If activity not found.
        """
        activity = self._get_activity_by_name(activity_name, session)
        return ActivityData.from_orm(activity)

    def _get_character_item(self, character_id: int, item_id: int, session: sqlalchemy.orm.Session) -> CharacterItem:
        character_item = (
            session.query(CharacterItem).filter_by(character_id=character_id, item_id=item_id).one_or_none()
        )
        if not character_item:
            character_item = CharacterItem(character_id=character_id, item_id=item_id)
            session.add(character_item)
            session.flush()
        return character_item

    @with_session
    def start_activity(
        self,
        character_name: str,
        activity_name: str,
        activity_option_name: str,
        session: sqlalchemy.orm.Session,
    ) -> Optional[CharacterActivityData]:
        """
        Start a new activity for a character. If an activity is already running, it is stopped first.
        Args:
            character_name: The name of the character.
            activity_name: The name of the activity to start.
            activity_option_name: The specific option for the activity.
            session: SQLAlchemy session (provided by decorator).
        Returns:
            None
        """
        character = self._get_character_by_name(character_name, session)
        current_activity = self._get_current_activity(character, session)
        if current_activity:
            self._stop_current_activity(character, session)
        new_activity = session.query(Activity).filter_by(activity_name=activity_name).one()
        activity_option: ActivityOption = (
            session.query(ActivityOption)
            .filter_by(activity_id=new_activity.activity_id, activity_option_name=activity_option_name)
            .one()
        )

        # For each skill requirement, check it against the character.
        requirements_not_met = []
        for skill_requirement in activity_option.skill_requirements:
            character_skill = self._get_character_skill(
                character,
                new_activity,
                session,
            )
            if character_skill.level < skill_requirement.required_level:
                requirements_not_met.append(
                    {
                        "skill_id": skill_requirement.skill_id,
                        "level_requirement": skill_requirement.required_level,
                        "character_skill_level": character_skill.level,
                    }
                )
        if requirements_not_met:
            raise ValueError(requirements_not_met)

        item_costs_not_met = []
        for item_cost in activity_option.item_costs:
            character_item: CharacterItem = self._get_character_item(character.character_id, item_cost.item_id, session)
            if item_cost.quantity > character_item.quantity:
                item_costs_not_met.append(
                    {
                        "item": item_cost.item_id,
                        "cost": item_cost.quantity,
                        "character_quantity": character_item.quantity,
                    }
                )
        if item_costs_not_met:
            raise ValueError(item_costs_not_met)

        character_activity = (
            session.query(CharacterActivity).filter_by(character_id=character.character_id).one_or_none()
        )
        new_character_activity = CharacterActivity(
            character_id=character.character_id,
            activity_id=new_activity.activity_id,
            activity_option_id=activity_option.activity_option_id,
        )
        session.add(new_character_activity)
        session.flush()
        return CharacterActivityData.from_orm(new_character_activity)

    def _stop_current_activity(self, character: Character, session: sqlalchemy.orm.Session) -> None:
        """
        Stop the current activity for a character, reward XP and items.
        Args:
            character_name: The name of the character.
            session: SQLAlchemy session.
        Returns:
            None
        """
        ended_at = pendulum.now("utc")
        current_activity = self._get_current_activity(character, session)
        if not current_activity:
            return

        activity_option = current_activity.activity_option
        activity_duration = ended_at.diff(ensure_utc(current_activity.started_at)).seconds
        session.delete(current_activity)

        # TODO: Remove workaround. Python doesn't like min of empty list, which happens when there's no item requirements.
        if activity_option.item_costs:
            item_cost_limits = []
            for item_cost in activity_option.item_costs:
                character_item = self._get_character_item(character.character_id, item_cost.item_id, session)
                item_cost_limits.append(character_item.quantity // item_cost.quantity)
            item_cost_limit = min(item_cost_limits)
            time_limit = activity_duration // activity_option.action_time
            actions_completed = min(item_cost_limit, time_limit)
        else:
            actions_completed = activity_duration // activity_option.action_time

        char_skill: CharacterSkill = (
            session.query(CharacterSkill)
            .filter_by(character_id=character.character_id, activity_id=current_activity.activity_id)
            .one()
        )

        character_activity_history = CharacterActivityHistory(
            character_id=character.character_id,
            activity_option_id=activity_option.activity_option_id,
            started_at=current_activity.started_at,
            ended_at=ended_at,
        )

        # Consume items based on actions completed
        for item_cost in activity_option.item_costs:
            chracter_item = self._get_character_item(character.character_id, item_cost.item_id, session)
            character_activity_history.item_costs.append(
                CharacterActivityItemCost(
                    character_activity_history_id=character_activity_history.character_activity_history_id,
                    item_id=item_cost.item_id,
                    quantity=item_cost.quantity,
                )
            )

            chracter_item.quantity -= item_cost.quantity * actions_completed

        # Reward experience
        for reward_experience in activity_option.reward_experience:
            char_skill.experience += actions_completed * reward_experience.experience
            character_activity_history.experience_rewards.append(
                CharacterActivityExperienceReward(
                    character_activity_history_id=character_activity_history.character_activity_history_id,
                    skill_id=reward_experience.skill_id,
                    experience=reward_experience.experience,
                )
            )

        # Reward items
        # For each item, give it to the character.
        for reward_item in activity_option.reward_items:
            character_activity_history.item_rewards.append(
                CharacterActivityItemReward(
                    character_activity_history_id=character_activity_history.character_activity_history_id,
                    item_id=reward_item.item_id,
                    quantity=reward_item.quantity,
                )
            )
            character_item = self._get_character_item(character.character_id, reward_item.item_id, session)
            character_item.quantity += reward_item.quantity * actions_completed

        session.add(character_activity_history)

    @with_session
    def get_current_activity(
        self, character_name: str, session: sqlalchemy.orm.Session
    ) -> Optional[CharacterActivityData]:
        """
        Get the current activity data for a character.
        Args:
            character_name: The name of the character.
            session: SQLAlchemy session (provided by decorator).
        Returns:
            CharacterActivityData or None if not found.
        """
        character = self._get_character_by_name(character_name, session)
        current_activity = self._get_current_activity(character, session)
        if not current_activity:
            return None
        return CharacterActivityData.from_orm(current_activity)

    @with_session
    def stop_current_activity(self, character_name, session: sqlalchemy.orm.Session) -> None:
        """
        Stop the current activity for a character.
        Args:
            character_name: The name of the character.
            session: SQLAlchemy session (provided by decorator).
        Returns:
            None
        """
        character = self._get_character_by_name(character_name, session)
        self._stop_current_activity(character, session)

    @with_session
    def get_all_characters(self, session: sqlalchemy.orm.Session) -> list[CharacterData]:
        """
        Get all characters in the database.
        Args:
            session: SQLAlchemy session (provided by decorator).
        Returns:
            List of CharacterData objects.
        """
        characters = session.query(Character).all()
        return [CharacterData.from_orm(character) for character in characters]

    @with_session
    def get_all_activities(self, session: sqlalchemy.orm.Session) -> list[ActivityData]:
        """
        Get all activities in the database.
        Args:
            session: SQLAlchemy session (provided by decorator).
        Returns:
            List of ActivityData objects.
        """
        activities = session.query(Activity).all()
        return [ActivityData.from_orm(activity) for activity in activities]

    @with_session
    def get_all_activity_options(self, activity_name: str, session: sqlalchemy.orm.Session) -> list[ActivityOptionData]:
        """
        Get all activity options for a given activity.
        Args:
            activity_name: The name of the activity.
            session: SQLAlchemy session (provided by decorator).
            character_name: (Optional) The name of the character (for filtering options).
        Returns:
            List of ActivityOptionData objects.
        """
        activity = session.query(Activity).filter_by(activity_name=activity_name).one()
        activity_options = session.query(ActivityOption).filter_by(activity_id=activity.activity_id).all()
        return [ActivityOptionData.from_orm(activity_option) for activity_option in activity_options]

    def _get_item_by_name(self, item_name: str, session: sqlalchemy.orm.Session) -> Item:
        return session.query(Item).filter_by(item_name=item_name).one()

    def _get_character_item_by_name(
        self, character_name: str, item_name: str, session: sqlalchemy.orm.Session
    ) -> CharacterItem:
        item = self._get_item_by_name(item_name, session)
        character = self._get_character_by_name(character_name, session)

        character_item = (
            session.query(CharacterItem)
            .filter_by(character_id=character.character_id, item_id=item.item_id)
            .one_or_none()
        )

        # If the CharacterItem doesn't exist yet, create it, and add it to the session.
        if not character_item:
            character_item = CharacterItem(character_id=character.character_id, item_id=item.item_id)
            session.add(character_item)
            session.flush()

        return character_item

    @with_session
    def get_character_item_by_name(
        self, character_name: str, item_name: str, session: sqlalchemy.orm.Session
    ) -> CharacterItemData:
        return CharacterItemData.from_orm(self._get_character_item_by_name(character_name, item_name, session))

    def _add_item_to_character(
        self, character_name: str, item_name: str, quantity: int, session: sqlalchemy.orm.Session
    ) -> None:
        character_item = self._get_character_item_by_name(character_name, item_name, session)
        character_item.quantity = quantity

    @with_session
    def add_item_to_character(
        self, character_name: str, item_name: str, quantity: int, session: sqlalchemy.orm.Session
    ) -> None:
        self._add_item_to_character(character_name, item_name, quantity, session)

    def _give_character_skill_xp(
        self, character_name: str, skill_name: str, experience: int, session: sqlalchemy.orm.Session
    ) -> None:
        """
        - Get the character skill
        - Update the xp
        """
        character_skill = self._get_character_skill_by_name(character_name, skill_name, session)
        character_skill.experience += experience
        session.flush()

    @with_session
    def give_character_skill_xp(
        self, character_name: str, skill_name: str, experience: int, session: sqlalchemy.orm.Session
    ) -> None:
        self._give_character_skill_xp(character_name, skill_name, experience, session)

    def _get_character_skill_by_name(
        self, character_name: str, skill_name: str, session: sqlalchemy.orm.Session
    ) -> CharacterSkill:
        skill = self._get_activity_by_name(activity_name=skill_name, session=session)
        character = self._get_character_by_name(character_name, session)
        character_skill = (
            session.query(CharacterSkill)
            .filter_by(character_id=character.character_id, activity_id=skill.activity_id)
            .one_or_none()
        )

        if not character_skill:
            character_skill = CharacterSkill(character_id=character.character_id, activity_id=skill.activity_id)
            session.add(character_skill)
        return character_skill

    @with_session
    def get_character_skill_by_name(
        self, character_name: str, skill_name: str, session: sqlalchemy.orm.Session
    ) -> CharacterSkillData:
        return CharacterSkillData.from_orm(self._get_character_skill_by_name(character_name, skill_name, session))
