import os

import pytest
import sqlalchemy

from idlescape.game import Game

TEST_DB_PATH = "test-game.db"


@pytest.fixture(scope="function")
def game():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    yield Game(f"sqlite:///{TEST_DB_PATH}")


def test_init_db(game: Game):
    inspector = sqlalchemy.inspect(game.engine)
    tables = inspector.get_table_names()
    expected_tables = {"characters", "activities", "character_activities"}
    for table in expected_tables:
        assert table in tables, f"Table '{table}' does not exist"


def test_create_character(game: Game):
    game.create_character(character_name="Tobyone")
    char = game.get_character_by_name("Tobyone")
    assert char is not None
    assert char.character_name == "Tobyone"


def test_get_activity_by_name(game: Game):
    activity = game.get_activity_by_name("mining")
    assert activity.activity_name == "mining"
    assert activity.activity_type == "skill"
    assert activity.activity_id == 1


def test_start_activity(game: Game):
    game.create_character(character_name="Tobyone")
    game.start_activity(character_name="Tobyone", activity_name="mining", activity_option_name="copper")
    current_activity = game.get_current_activity(character_name="Tobyone")
    print(current_activity)
    assert current_activity.activity_id == 1
    assert current_activity.started_at is not None

    # Starting an activity when one is already going SHOULD end the previous activity.
    game.start_activity(character_name="Tobyone", activity_name="woodcutting", activity_option_name="tree")
    current_activity = game.get_current_activity(character_name="Tobyone")
    assert current_activity.activity_id == 2
    assert current_activity.activity_option_id == 3
    assert current_activity.started_at is not None


def test_stop_current_activity(game: Game):
    game.create_character(character_name="Tobyone")
    game.start_activity(character_name="Tobyone", activity_name="mining", activity_option_name="copper")
    game.stop_current_activity(character_name="Tobyone")
    current_activity = game.get_current_activity(character_name="Tobyone")
    assert current_activity is None


def test_multiple_characters(game: Game):
    game.create_character(character_name="Alice")
    game.create_character(character_name="Bob")
    alice = game.get_character_by_name("Alice")
    bob = game.get_character_by_name("Bob")
    assert alice.character_name == "Alice"
    assert bob.character_name == "Bob"
    assert alice.character_id != bob.character_id


def test_start_and_stop_activity_multiple_characters(game: Game):
    game.create_character(character_name="Alice")
    game.create_character(character_name="Bob")
    game.start_activity(character_name="Alice", activity_name="mining", activity_option_name="copper")
    game.start_activity(character_name="Bob", activity_name="woodcutting", activity_option_name="tree")
    alice_activity = game.get_current_activity(character_name="Alice")
    bob_activity = game.get_current_activity(character_name="Bob")
    assert alice_activity.activity.activity_name == "mining"
    assert bob_activity.activity.activity_name == "woodcutting"
    game.stop_current_activity(character_name="Alice")
    assert game.get_current_activity(character_name="Alice") is None
    assert game.get_current_activity(character_name="Bob") is not None


def test_reward_experience_and_items(game: Game):
    game.create_character(character_name="Alice")
    game.start_activity(character_name="Alice", activity_name="mining", activity_option_name="copper")
    # Simulate time passing by stopping the activity
    game.stop_current_activity(character_name="Alice")
    char = game.get_character_by_name("Alice")
    # Check that Alice has some experience in mining
    mining_skill = next((s for s in char.skills if s.skill.activity_name == "mining"), None)
    assert mining_skill is not None
    assert mining_skill.experience >= 0
    # Check that Alice has the reward item (iron)
    copper_item = next((item for item in char.items if item.item.item_name == "copper"), None)
    assert copper_item is not None
    assert copper_item.item is not None
    assert copper_item.item.item_name == "copper"
    assert copper_item.character_item_id is not None


def test_give_items(game: Game):
    """
    1. Create Bob
    2. Give Bob 1 iron
    3. Assert Bob has 1 iron
    4. Assert Bob has 0 coal
    """
    bob = game.create_character("Bob")
    game.add_item_to_character("Bob", "iron", 1)
    bobs_iron = game.get_character_item_by_name("Bob", "iron")
    assert bobs_iron.item.item_name == "iron"
    assert bobs_iron.quantity == 1

    bobs_coal = game.get_character_item_by_name("Bob", "coal")
    assert bobs_coal.item.item_name == "coal"
    assert bobs_coal.quantity == 0


def test_give_character_skills(game: Game):
    """
    1. Create Bob
    2. Give Bob level 15 mining.
    3. Assert Bob has level 15 mining.
    4. Assert Bob has xp.
    5. Give Bob xp to get to level 60.
    6. Assert that Bob has the right xp and level.
    """
    game.create_character("Bob")
    game.give_character_skill_xp("Bob", "mining", 1_154)
    bobs_mining = game.get_character_skill_by_name("Bob", "mining")
    assert bobs_mining.experience == 1_154
    assert bobs_mining.level == 10

    game.give_character_skill_xp("Bob", "mining", 68_023 - 1_154)
    bobs_mining = game.get_character_skill_by_name("Bob", "mining")
    assert bobs_mining.experience == 68_023
    assert bobs_mining.level == 60
