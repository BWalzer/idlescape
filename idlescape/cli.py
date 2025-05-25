import click
from idlescape.game import Game


DEFAULT_DB_PATH = "sqlite:///idlescape.db"


@click.group()
@click.option("--db-path", default=DEFAULT_DB_PATH, help="Database path for the game")
def cli(db_path: str):
    global game
    game = Game(db_path)


@cli.command(
    "create-character",
    help="Create a new character",
)
@click.argument("character-name")
def create_character(character_name: str) -> None:
    char = game.create_character(character_name)
    click.echo(f"Created Character: {char.character_name}")


@cli.command(
    "show-character",
    help="Show all information of a character",
)
@click.argument("character-name")
def show_character(character_name: str) -> None:
    char = game.get_character_by_name(character_name)
    if char:
        click.echo(char)
    else:
        click.echo(f"Could not find a character with the name '{character_name}'")


@cli.command(
    "start-activity",
    help="Start an activity for a character",
)
@click.argument("character_name")
@click.argument("activity_name")
def start_activity(character_name: str, activity_name: str) -> None:
    game.start_activity(character_name=character_name, activity_name=activity_name)
    click.echo(f"{character_name} started {activity_name}")


@cli.command("stop-activity", help="Stop the current activity for a character")
@click.argument("character_name")
def stop_activity(character_name: str) -> None:
    game.stop_current_activity(character_name=character_name)


@cli.command("list-characters", help="List all available characters")
def list_characters() -> None:
    characters = game.get_all_characters()
    for character in characters:
        click.echo(
            f"{character.character_name} - Created {character.created_at}, {character.created_at.diff_for_humans()}"
        )
