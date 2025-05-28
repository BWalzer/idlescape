import click
import questionary
from questionary import Style

from idlescape.game import Game

DEFAULT_DB_PATH = "sqlite:///idlescape.db"

# Define a custom style for questionary with highlighted selection and surrounding text
custom_style = Style(
    [
        ("selected", "fg:#ffffff bg:#0077cc bold"),  # Highlighted option
        ("pointer", "fg:#00ff00 bold"),  # The pointer (>)
        ("question", "fg:#00ffff bold"),  # The question text
        ("answer", "fg:#00ff00 bold"),  # The answer text
        ("highlighted", "fg:#0077cc bold"),  # Highlighted text around selection
        ("separator", "fg:#666666"),  # Separator lines
        ("instruction", "fg:#888888 italic"),  # Instructions
    ]
)


@click.command()
@click.option("--db-path", default=DEFAULT_DB_PATH, help="Database path for the game")
def cli(db_path: str):
    game = Game(db_path)
    actions = [
        "Create Character",
        "Show Character",
        "Start Activity",
        "Stop Activity",
        "List Characters",
        "Exit",
    ]

    while True:
        action = questionary.select("What would you like to do?", choices=actions, style=custom_style).ask()

        if action == "Create Character":
            char_name = questionary.text("Enter new character name", style=custom_style).ask()
            char = game.create_character(char_name)
            click.echo(f"Created Character: {char.character_name}")

        elif action == "Show Character":
            char_names = [char.character_name for char in game.get_all_characters()]
            if not char_names:
                click.echo("No characters available.")
                continue
            char_name = questionary.select("Choose a character", choices=char_names, style=custom_style).ask()
            char = game.get_character_by_name(char_name)
            if char:
                click.echo(char)
            else:
                click.echo(f"Could not find a character with the name '{char_name}'")

        elif action == "Start Activity":
            char_names = [char.character_name for char in game.get_all_characters()]
            if not char_names:
                click.echo("No characters available.")
                continue
            char_name = questionary.select("Choose a character", choices=char_names, style=custom_style).ask()

            activities = [activity.activity_name for activity in game.get_all_activities()]
            activity = questionary.select("Enter activity name", choices=activities, style=custom_style).ask()

            activity_options = [
                activity_option.activity_option_name for activity_option in game.get_all_activity_options(activity)
            ]
            activity_option = questionary.select(
                "Choose an activity option", choices=activity_options, style=custom_style
            ).ask()

            result = game.start_activity(
                character_name=char_name,
                activity_name=activity,
                activity_option_name=activity_option,
            )
            if not result:
                click.echo(f"Couldn't start {activity} - {activity_option}. Double check the skill requirements.")
                continue
            click.echo(f"{char_name} started {result.activity.activity_name} - {activity_option}")

        elif action == "Stop Activity":
            char_names = [char.character_name for char in game.get_all_characters()]
            if not char_names:
                click.echo("No characters available.")
                continue
            char_name = questionary.select("Choose a character", choices=char_names, style=custom_style).ask()
            game.stop_current_activity(character_name=char_name)
            click.echo(f"Stopped current activity for {char_name}")

        elif action == "List Characters":
            characters = game.get_all_characters()
            if not characters:
                click.echo("No characters available.")
            for character in characters:
                click.echo(
                    f"{character.character_name} - Created {character.created_at}, {character.created_at.diff_for_humans()}"
                )

        elif action == "Exit":
            break


if __name__ == "__main__":
    cli()
