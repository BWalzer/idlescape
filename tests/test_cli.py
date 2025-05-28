# import os

# import pytest
# from click.testing import CliRunner

# from idlescape.cli import cli

# TEST_DB_PATH = "test-cli.db"


# @pytest.fixture(autouse=True, scope="module")
# def clean_cli_db():
#     if os.path.exists(TEST_DB_PATH):
#         os.remove(TEST_DB_PATH)
#     yield


# @pytest.fixture(scope="function")
# def runner():
#     return CliRunner()


# def test_create_character_cli(runner):
#     result = runner.invoke(cli, ["--db-path", f"sqlite:///{TEST_DB_PATH}", "create-character", "Tobyone"])
#     assert result.exit_code == 0
#     assert result.output == "Created Character: Tobyone\n"


# def test_show_character_cli(runner):
#     result = runner.invoke(cli, ["--db-path", f"sqlite:///{TEST_DB_PATH}", "show-character", "Tobyone"])
#     assert result.exit_code == 0
#     assert "Name: Tobyone" in result.output
#     result = runner.invoke(cli, ["--db-path", f"sqlite:///{TEST_DB_PATH}", "show-character", "Tobytwo"])
#     assert result.exit_code == 0
#     assert result.output == "Could not find a character with the name 'Tobytwo'\n"


# def test_start_activity_cli(runner):
#     result = runner.invoke(cli, ["--db-path", f"sqlite:///{TEST_DB_PATH}", "start-activity", "Tobyone", "mining"])
#     assert result.exit_code == 0
#     assert result.output == "Tobyone started mining\n"
