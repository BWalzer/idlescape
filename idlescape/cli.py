# TODO:
#   - Move all game logic out of here, this should just be the interface. This file shouldn't interact with sqlalchemy. This is just the front end.

from idlescape.character import (
    Character,
    _init_db,
    CharacterActivity,
    Activity,
)
import click
import sqlalchemy
import sqlalchemy.orm
import sys

ENGINE = sqlalchemy.create_engine("sqlite:///idlescape.db")
DEBUG = True


@click.group()
def cli():
    Activity.load_activities()


@cli.command("list-characters", help="List all characters")
def list_characters() -> None:
    with sqlalchemy.orm.Session(ENGINE) as session:
        characters = session.query(Character).all()

        click.echo("\n".join([char.character_name for char in characters]))


@cli.command(
    "create-character",
    help="Create a new character",
)
@click.argument("character-name")
def create_character(character_name: str) -> None:
    with sqlalchemy.orm.Session(ENGINE) as session:
        # Create a new character and initialize its skills
        char = Character(character_name=character_name)

        # Add the character to the session
        session.add(char)

        session.commit()
        click.echo(f"Created Character: {char.character_name}")


@cli.command(
    "show-character",
    help="Show all information of a character",
)
@click.argument("character-name")
def show_character(character_name: str) -> None:
    char = Character.get_character_by_name(character_name)
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
    activity = Activity.get_activity_by_name(activity_name)
    char = Character.get_character_by_name(character_name)
    if not char:
        click.echo(f"Could not find a character with the name '{character_name}'")
        sys.exit()

    char.stop_current_activity()
    char.start_activity(activity)
    new_activity = CharacterActivity(  # noqa
        character_id=char.character_id,
        activity_id=activity.activity_id,
    )
    char.save()


@cli.command(
    "init-db",
    help="Initialize the game DB, wiping existing data",
)
def init_db() -> None:
    _init_db()


if __name__ == "__main__":
    cli()
