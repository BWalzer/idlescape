# TODO
## Game Features
In _rough_ order of when they'll be added.
- [x] Add character skill xp
- [ ] Results from ending a skill
    - [x] Gain xp
    - [x] Add different options for actions within a skill. Differ xp gain.
    - [x] Obtain resources
- [x] Add levels to skills
- [ ] Add requirements and costs to skills
    - [ ] Requirements
        - [x] skills
        - [ ] items
        - [ ] quests (after quests)
    - [ ] Costs: Items (crafting skills)
- [ ] Activity history
    - [ ] Character activity rewards (xp, items)
- [ ] Combat
    - [ ] Equipment
    - [ ] Skills
        - [ ] hitpoints
        - [ ] melee
    - [ ] Enemy monsters
    - [ ] Enemy drops
    - [ ] DEATH
- [ ] Quests
- [ ] Skill improvements
    - [ ] Tools boost action rate
    - [ ] Levels boost action rate
    - [ ]

## Interface
- [ ] CLI
    - [ ] Output all handled from the CLI, not from Game
    - [ ] Prettier output formatting. Colors, bold, italics, etc.
- [ ] Web app. Streamlit?
- [ ] Discord bot

## Dev stuff
- [ ] Testing
    - [ ] 100% code coverage
- [ ] Handle DB errors better. This should be on the front end
- [ ] Make `Game` independent of backend implementation (i.e., no session reference in `Game` class)
    - This might not be worth it. The idea is to be able to swap in other relation databases as the backend, without altering the game code. SQLAlchemy should help a lot with this.
    - Maybe support non-SQL databases as well? Again, not sure if this is worth anything.
