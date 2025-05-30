[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/BWalzer/idlescape/main.svg)](https://results.pre-commit.ci/latest/github/BWalzer/idlescape/main)

# TODO
## Game Features
In _rough_ order of when they'll be added.
- [x] Add character skill xp
- [x] Results from ending a skill
    - [x] Gain xp
    - [x] Add different options for actions within a skill. Differ xp gain.
    - [x] Obtain resources
- [x] Add levels to skills
- [ ] Add requirements and costs to skills
    - [ ] Requirements
        - [x] skills
        - [x] items
    - [x] Costs: Items (crafting skills)
- [ ] Activity history
    - [x] Rewarded items
    - [x] Rewarded XP
    - [x] Item Costs
    - [ ] Make it pretty
- [ ] Combat
    - [ ] Equipment
    - [ ] Skills
        - [ ] hitpoints
        - [ ] melee
    - [ ] Enemy monsters
    - [ ] Enemy drops
    - [ ] DEATH
- [ ] Quests
    - [ ] Add quests to activity requirements
- [ ] Skill improvements
    - [ ] Tools boost action rate
    - [ ] Levels boost action rate
    - **more skills**
        - [ ] fletching


## Interface
- [ ] Add name rules
    - Can't be empty
    - utf-8
    - no invisible chars
- [ ] CLI
    - [ ] Output all handled from the CLI, not from Game
    - [ ] Prettier output formatting. Colors, bold, italics, etc.
- [ ] Web app. Streamlit?
- [ ] Discord bot

## Dev stuff
- [x] Clean up ORM classes and DTOs. DTOs shouldn't need the session, make the relationship in the ORM.
- [ ] Refactor DTOs to better suit the application
    - [ ] Combine ActivityOptionData with it's requirements
    - [x] Add items and skills to the CharacterData object
- [ ] Testing
    - [ ] 100% code coverage
- [ ] Handle DB errors better. This should be on the front end
- [ ] Make `Game` independent of backend implementation (i.e., no session reference in `Game` class)
    - This might not be worth it. The idea is to be able to swap in other relation databases as the backend, without altering the game code. SQLAlchemy should help a lot with this.
    - Maybe support non-SQL databases as well? Again, not sure if this is worth anything.
