def _spec_to_rgba(class_name: str, ratio: float) -> str:
    return (
        "rgba("
        + ",".join([str(round(c * ratio)) for c in _PROFESSION_COLOR_MAP[class_name]])
        + ",1)"
    )


_PROFESSION_COLOR_MAP = {
    "guardian": [7, 65, 65],
    "warrior": [75, 58, 17],
    "engineer": [80, 40, 1],
    "ranger": [33, 65, 7],
    "thief": [51, 25, 30],
    "elementalist": [80, 1, 1],
    "mesmer": [75, 12, 60],
    "necromancer": [4, 57, 35],
    "revenant": [37, 1, 13],
}


spec_color_map = {
    "Guardian": _spec_to_rgba("guardian", 1.2),
    "Dragonhunter": _spec_to_rgba("guardian", 1.7),
    "Firebrand": _spec_to_rgba("guardian", 2.2),
    "Willbender": _spec_to_rgba("guardian", 2.7),
    "Luminary": _spec_to_rgba("guardian", 3.2),
    "Revenant": _spec_to_rgba("revenant", 1.2),
    "Herald": _spec_to_rgba("revenant", 1.7),
    "Renegade": _spec_to_rgba("revenant", 2.2),
    "Vindicator": _spec_to_rgba("revenant", 2.7),
    "Conduit": _spec_to_rgba("revenant", 3.2),
    "Warrior": _spec_to_rgba("warrior", 1.2),
    "Berserker": _spec_to_rgba("warrior", 1.7),
    "Spellbreaker": _spec_to_rgba("warrior", 2.2),
    "Bladesworn": _spec_to_rgba("warrior", 2.7),
    "Paragon": _spec_to_rgba("warrior", 3.2),
    "Engineer": _spec_to_rgba("engineer", 1.2),
    "Scrapper": _spec_to_rgba("engineer", 1.7),
    "Holosmith": _spec_to_rgba("engineer", 2.2),
    "Mechanist": _spec_to_rgba("engineer", 2.7),
    "Amalgam": _spec_to_rgba("engineer", 3.2),
    "Ranger": _spec_to_rgba("ranger", 1.2),
    "Druid": _spec_to_rgba("ranger", 1.7),
    "Soulbeast": _spec_to_rgba("ranger", 2.2),
    "Untamed": _spec_to_rgba("ranger", 2.7),
    "Galeshot": _spec_to_rgba("ranger", 3.2),
    "Thief": _spec_to_rgba("thief", 1.2),
    "Daredevil": _spec_to_rgba("thief", 1.7),
    "Deadeye": _spec_to_rgba("thief", 2.2),
    "Specter": _spec_to_rgba("thief", 2.7),
    "Antiquary": _spec_to_rgba("thief", 3.2),
    "Elementalist": _spec_to_rgba("elementalist", 1.2),
    "Tempest": _spec_to_rgba("elementalist", 1.7),
    "Weaver": _spec_to_rgba("elementalist", 2.2),
    "Catalyst": _spec_to_rgba("elementalist", 1.7),
    "Evoker": _spec_to_rgba("elementalist", 3.2),
    "Mesmer": _spec_to_rgba("mesmer", 1.2),
    "Chronomancer": _spec_to_rgba("mesmer", 1.7),
    "Mirage": _spec_to_rgba("mesmer", 2.2),
    "Virtuoso": _spec_to_rgba("mesmer", 2.7),
    "Troubadour": _spec_to_rgba("mesmer", 3.2),
    "Necromancer": _spec_to_rgba("necromancer", 1.2),
    "Reaper": _spec_to_rgba("necromancer", 1.7),
    "Scourge": _spec_to_rgba("necromancer", 2.2),
    "Harbinger": _spec_to_rgba("necromancer", 2.7),
    "Ritualist": _spec_to_rgba("necromancer", 3.2),
}
