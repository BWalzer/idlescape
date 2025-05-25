import pytest
import sqlalchemy
from idlescape.game import Game
import os

TEST_DB_PATH = "test-idlescape.db"


@pytest.fixture(scope="session")
def game():
    yield Game(f"sqlite:///{TEST_DB_PATH}")

    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


def test_init_db(game: Game):
    inspector = sqlalchemy.inspect(game.engine)
    tables = inspector.get_table_names()
    expected_tables = {"characters", "activities", "character_activities"}
    for table in expected_tables:
        assert table in tables, f"Table '{table}' does not exist"


def test_create_character(game: Game):
    """
    Create a character. Commit. Check if sqlalchemy can find the character, and the name matches.
    """
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
    game.start_activity(character_name="Tobyone", activity_name="mining")
    current_activity = game.get_current_activity(character_name="Tobyone")
    print(current_activity)
    assert current_activity.activity_id == 1
    assert current_activity.started_at is not None
    assert current_activity.ended_at is None


def test_stop_current_activity(game: Game):
    game.stop_current_activity(character_name="Tobyone")
    current_activity = game.get_current_activity(character_name="Tobyone")
    assert current_activity is None
