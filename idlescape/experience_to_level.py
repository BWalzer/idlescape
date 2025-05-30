import importlib
import json


def xp_to_level(experience: int) -> int:
    with importlib.resources.open_text("idlescape.data", "experience_to_level.json") as f:
        xp_level_table = json.load(f)

    for level in reversed(xp_level_table):
        if experience >= level["min_xp"]:
            return level["level"]
    return 1
