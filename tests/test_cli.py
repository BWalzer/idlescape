from idlescape.cli import cli
from click.testing import CliRunner
import os
import pytest

TEST_DB_PATH = "test-cli.db"


@pytest.fixture(autouse=True, scope="module")
def clean_cli_db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    yield
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


def test_create_character_cli():
    runner = CliRunner()
    result = runner.invoke(cli, ["--db-path", f"sqlite:///{TEST_DB_PATH}", "create-character", "Tobyone"])
    assert result.exit_code == 0
    assert result.output == "Created Character: Tobyone\n"
