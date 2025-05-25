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
