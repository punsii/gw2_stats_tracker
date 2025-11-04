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
    "Guardian": _spec_to_rgba("guardian", 1.5),
    "Dragonhunter": _spec_to_rgba("guardian", 2.0),
    "Firebrand": _spec_to_rgba("guardian", 2.5),
    "Willbender": _spec_to_rgba("guardian", 3.0),
    "Luminary": _spec_to_rgba("guardian", 3.5),
    "Revenant": _spec_to_rgba("revenant", 1.5),
    "Herald": _spec_to_rgba("revenant", 2.0),
    "Renegade": _spec_to_rgba("revenant", 2.5),
    "Vindicator": _spec_to_rgba("revenant", 3.0),
    "Conduit": _spec_to_rgba("revenant", 3.5),
    "Warrior": _spec_to_rgba("warrior", 1.5),
    "Berserker": _spec_to_rgba("warrior", 2.0),
    "Spellbreaker": _spec_to_rgba("warrior", 2.5),
    "Bladesworn": _spec_to_rgba("warrior", 3.0),
    "Paragon": _spec_to_rgba("warrior", 3.5),
    "Engineer": _spec_to_rgba("engineer", 1.5),
    "Scrapper": _spec_to_rgba("engineer", 2.0),
    "Holosmith": _spec_to_rgba("engineer", 2.5),
    "Mechanist": _spec_to_rgba("engineer", 3.0),
    "Amalgam": _spec_to_rgba("engineer", 3.5),
    "Ranger": _spec_to_rgba("ranger", 1.5),
    "Druid": _spec_to_rgba("ranger", 2.0),
    "Soulbeast": _spec_to_rgba("ranger", 2.5),
    "Untamed": _spec_to_rgba("ranger", 3.0),
    "Galeshot": _spec_to_rgba("ranger", 3.5),
    "Thief": _spec_to_rgba("thief", 1.5),
    "Daredevil": _spec_to_rgba("thief", 2.0),
    "Deadeye": _spec_to_rgba("thief", 2.5),
    "Specter": _spec_to_rgba("thief", 3.0),
    "Antiquary": _spec_to_rgba("thief", 3.5),
    "Elementalist": _spec_to_rgba("elementalist", 1.5),
    "Tempest": _spec_to_rgba("elementalist", 2.0),
    "Weaver": _spec_to_rgba("elementalist", 2.5),
    "Catalyst": _spec_to_rgba("elementalist", 2.0),
    "Evoker": _spec_to_rgba("elementalist", 3.5),
    "Mesmer": _spec_to_rgba("mesmer", 1.5),
    "Chronomancer": _spec_to_rgba("mesmer", 2.0),
    "Mirage": _spec_to_rgba("mesmer", 2.5),
    "Virtuoso": _spec_to_rgba("mesmer", 3.0),
    "Troubadour": _spec_to_rgba("mesmer", 3.5),
    "Necromancer": _spec_to_rgba("necromancer", 1.5),
    "Reaper": _spec_to_rgba("necromancer", 2.0),
    "Scourge": _spec_to_rgba("necromancer", 2.5),
    "Harbinger": _spec_to_rgba("necromancer", 3.0),
    "Ritualist": _spec_to_rgba("necromancer", 3.5),
}
