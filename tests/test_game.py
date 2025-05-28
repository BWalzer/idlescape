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
    game.start_activity(character_name="Tobyone", activity_name="mining", activity_option_name="iron")
    current_activity = game.get_current_activity(character_name="Tobyone")
    print(current_activity)
    assert current_activity.activity_id == 1
    assert current_activity.started_at is not None
    assert current_activity.ended_at is None

    # Starting an activity when one is already going SHOULD end the previous activity.
    game.start_activity(character_name="Tobyone", activity_name="woodcutting", activity_option_name="tree")
    current_activity = game.get_current_activity(character_name="Tobyone")
    assert current_activity.activity_id == 2
    assert current_activity.activity_option_id == 3
    assert current_activity.started_at is not None
    assert current_activity.ended_at is None


def test_stop_current_activity(game: Game):
    game.create_character(character_name="Tobyone")
    game.start_activity(character_name="Tobyone", activity_name="mining", activity_option_name="coal")
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
    game.start_activity(character_name="Alice", activity_name="mining", activity_option_name="iron")
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
    game.start_activity(character_name="Alice", activity_name="mining", activity_option_name="iron")
    # Simulate time passing by stopping the activity
    game.stop_current_activity(character_name="Alice")
    char = game.get_character_by_name("Alice")
    # Check that Alice has some experience in mining
    mining_skill = next((s for s in char.skills if s.activity.activity_name == "mining"), None)
    assert mining_skill is not None
    assert mining_skill.experience >= 0
    # Check that Alice has the reward item (iron)
    iron_item = next((item for item in char.items if item.item.item_name == "iron"), None)
    assert iron_item is not None
    assert iron_item.item.item_name == "iron"
    assert iron_item.item_id is not None
    assert iron_item.character_id == char.character_id
    assert iron_item.character_item_id is not None
    assert iron_item.item is not None
    assert iron_item.item.item_id is not None
    assert iron_item.item.item_name == "iron"
    assert iron_item.created_at is not None
    assert iron_item.updated_at is not None
