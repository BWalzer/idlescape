import json


def xp_to_level(experience: int) -> int:
    with open("idlescape/data/experience_to_level.json", "r") as f:
        xp_level_table = json.load(f)

    for level in reversed(xp_level_table):
        if experience >= level["min_xp"]:
            return level["level"]
    return 1
