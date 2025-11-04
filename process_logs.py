from typing import List

import pandas as pd

from color_lib import spec_color_map


class FightInvalidException(Exception):
    pass


# logList.keys()=dict_keys([
#   'pages'
#   'totalUploads'
#   'userToken'
#   'uploads'
# ])

# _RELEVANT_KEYS_METADATA = [
#     # logList['uploads'][0].keys()=dict_keys([
#     "id",
#     "permalink",
#     "uploadTime",
#     "encounterTime",
#     #  'generator'
#     #  'generatorId'
#     #  'generatorVersion'
#     #  'language'
#     #  'languageId'
#     #  'evtc'
#     #  'players' The player list is also part or the dataset
#     #  'encounter'
#     #  'report'
#     #  'tempApiId'
#     # ])
# ]

_RELEVANT_KEYS_DATA = [
    "timeStart",
    "timeEnd",
    "duration",
    "players",
]

_RELEVANT_KEYS_DATA_PLAYERS = [
    "account",
    "group",
    "hasCommanderTag",
    "profession",
    "support",
    "groupBuffsActive",
    "squadBuffsActive",
    "buffUptimesActive",
    "consumables",
    "activeTimes",
    "extHealingStats",
    "extBarrierStats",
    "name",
    # "healing", XXX -> always 0 or 10
    "dpsAll",
    "statsAll",
    # "outgoingHealing" XXX does not show up anymore?
]

BOON_IDS = {
    717: "Protection",
    718: "Regeneration",
    719: "Swiftness",
    725: "Fury",
    726: "Vigor",
    740: "Might",
    743: "Aegis",
    873: "Resolution",
    1122: "Stability",
    1187: "Quickness",
    26980: "Resistance",
    30328: "Alacrity",
    5974: "Superspeed",
    10332: "ChaosAura",
    5577: "ShockAura",
    5579: "FrostAura",
    5677: "FireAura",
    5684: "MagnetAura",
}
_BOON_CATEGORIES_IN = ["groupBuffsActive", "squadBuffsActive", "buffUptimesActive"]
BOON_CATEGORIES_OUT = [" (Group Generation/s)", " (Squad Generation/s)", " (Uptime%)"]
_BOON_SELECTORS = ["generation", "generation", "uptime"]

BOON_KEYS = sorted(
    [id + postfix for postfix in BOON_CATEGORIES_OUT for id in BOON_IDS.values()]
) + ["Bufffood (uptime%)"]

# These are keys where i dont see a scenario in which they would
# contain relevant information that another key would not also contain.
_DROP_KEYS = [
    "damage",  # -> dps
    "condiDamage",  # -> condiDps
    "powerDamage",  # -> powerDps
    "breakbarDamage",  # -> always 0
    "avgBoons",  # -> avgActiveBoons
    "avgConditions",  # -> avgActiveConditions
    "actorDps",  # -> almost the same as dps
    "againstMovingRate",  # --> always 0
    "againstDownedCount",  # -> not relevant
    "againstDownedDamage",  # -> not relevant
    "actorDamage",  # -> ...
    "actorCondiDps",  # -> ...
    "actorCondiDamage",  # -> ...
    "actorPowerDps",  # -> ...
    "actorPowerDamage",  # -> ...
    "actorBreakbarDamage",  # -> ...
    "condiCleanseTime",  # -> condiCleanse
    "condiCleanseTimeSelf",  # -> ...
    "boonStripsTime",  # -> ...
    "totalDmg",  # --> 'dps' should be enough
    "directDamageCount",  # --> totalDmgCount
    "directDmg",  # --> just use dps
    "connectedConditionCount",  # -> litterally no one cares
    "connectedConditionDamage",  # -> litterally no one cares
    "connectedConditionAbove90HPCount",  # -> ...
    "connectedConditionAbove90HPDamage",  # -> ...
    "connectedLifeLeechCount",  # -> litterally no one cares
    "connectedLifeLeechDamage",  # -> litterally no one cares
    "connectedPowerCount",  # -> totalDmgCount
    "connectedPowerDamage",  # -> totalDmg
    "connectedPowerAbove90HPCount",  # -> ...
    "connectedPowerAbove90HPDamage",  # -> maybe someday if i feel like it
    "connectedDamageCount",  # -> totalDmgCount
    "connectedDmg",  # --> just use dps
    "connectedDirectDamageCount",  # -> totalDmgCount
    "connectedDirectDmg",  # --> just use dps
    "critableDirectDamageCount",  # -> totalDmgCount
    "stackDist",  # ->  XXX was NaN sometimes, see below
    "wasted",  # -> don't know what it means
    "saved",  # -> don't know what it means
    "timeWasted",  # -> don't know what it means
    "timeSaved",  # -> don't know what it means
]

# Values that need to be divided by the active time (how long the player actually participated)
_DIVIDE_BY_TIME_KEYS = [
    "resurrects",
    "resurrectTime",
    "condiCleanse",
    "condiCleanseSelf",
    "boonStrips",
    "boonStripDownContribution",
    "boonStripDownContributionTime",
    "stunBreak",
    "removedStunDuration",
    "appliedCrowdControl",
    "appliedCrowdControlDownContribution",
    "appliedCrowdControlDuration",
    "appliedCrowdControlDurationDownContribution",
    "swapCount",
    "totalDamageCount",
    "criticalDmg",
    "missed",
    "evaded",
    "blocked",
    "interrupts",
    "invulned",
    "killed",
    "downed",
    "downContribution",
]
_INTERMEDIATE_KEYS = [
    "duration",
    "hasCommanderTag",
    "group",
    "activeTimes",
    "timeEnd",
]

RENAMED_KEYS = {
    "dps": "Damage (/s)",
    "downContribution": "Down Contribution Damage (/s)",
    "condiDps": "Condition Damage (/s)",
    "powerDps": "Power Damage (/s)",
    "resurrects": "Resurrects (/s)",
    "resurrectTime": "Resurrect Time (/s)",
    "condiCleanse": "Condition Cleanse (/s)",
    "condiCleanseSelf": "Condition CleanseSelf (/s)",
    "stunBreak": "Stun Breaks (/s)",
    "removedStunDuration": "Removed Stun Duration (/s)",
    "boonStrips": "Boon Strips (/s)",
    "boonStripDownContribution": "Boon Strip Down Contribution (/s)",
    "boonStripDownContributionTime": "Boon Strip Down Contribution Time (/s)",
    "wasted": "Wasted",
    "timeWasted": "Time Wasted (/s)",
    "saved": "Saved",
    "timeSaved": "Time Saved (/s)",
    "distToCom": "Distance To Commander  (avg)",
    "avgActiveBoons": "Active Boons  (avg)",
    "avgActiveConditions": "Active Conditions (avg)",
    "swapCount": "Weapon Swaps (/s)",
    "skillCastUptime": "Skill Cast Uptime (%)",
    "skillCastUptimeNoAA": "Skill Cast Uptime - No Autoattack (%)",
    "totalDamageCount": "Damage Count (/s)",
    "criticalRate": "Critical Rate (avg)",
    "criticalDmg": "Critical Damage (/s)",
    "flankingRate": "Flanking Rate (avg)",
    "glanceRate": "Glance Rate (avg)",
    "missed": "Hits Missed (/s)",
    "evaded": "Hits Evaded (/s)",
    "blocked": "Hits Blocked (/s)",
    "invulned": "Hits Invulned (/s)",
    "appliedCrowdControl": "Crowd Control (/s)",
    "appliedCrowdControlDownContribution": "Crowd Control Down Contribution (/s)",
    "appliedCrowdControlDuration": "Crowd Control Duration (/s)",
    "appliedCrowdControlDurationDownContribution": "Crowd Control Duration Down Contribution (/s)",
    "interrupts": "Interrupts (/s)",
    "killed": "Kills (/s)",
    "downed": "Downed (/s)",
    "downedHealing": "Healing To Downed (/s)",
    "healing": "Healing (/s)",
    "barrier": "Barrier (/s)",
    "percentageAlive": "Time Alive (%)",
}


def explode_apply(df: pd.DataFrame, column: str):
    new_columns = df.explode(column)[column].apply(pd.Series)
    if df.shape[0] != new_columns.shape[0]:
        raise FightInvalidException("Multiple fights in one log detected!")
    return pd.concat([df.drop(columns=[column]), new_columns], axis=1)


def transform_log(log: dict, log_id: str) -> pd.DataFrame:
    df = pd.DataFrame({k: [v] for k, v in ({"id": log_id} | log).items()})

    # create a separate row for each player of a fight
    players = df.explode("players")["players"].apply(pd.Series)
    # and join to original dataFrame
    df = df.drop(columns=["players"])
    df = df.join(players)

    df["activeTimes"] = df["activeTimes"].apply(lambda x: x[0] / 1000)

    # create a separate column for each stat
    for column in ["dpsAll", "support", "statsAll"]:
        df = explode_apply(df, column)

    # filter out players that did not acually participate in the fight
    df = df[
        (df["dps"] >= 50)
        | (df["blocked"] >= 5)
        | (df["evaded"] >= 5)
        | (df["boonStrips"] >= 5)
        | (df["condiCleanse"] >= 10)
    ]
    # filter out unknown players (pl-*)
    df = df[~df["account"].str.startswith("Non Squad Player")]
    if df.size == 0:
        # No players actually participated...
        raise FightInvalidException(f"Log {log_id} contains no active players!")
    for column in _BOON_CATEGORIES_IN:
        if column not in df:
            # too lazy to think about what to do here
            raise FightInvalidException(f"Log {log_id} does not contain {column}!")

    # Same idea for the boons, but we have a more complicated data structure to begin with:
    # "groupBuffsActive": [
    #   {
    #     "id": 1187,
    #     "buffData": [{
    #       "generation": 12.87,
    #       "overstack": 12.87,
    #       "wasterd": 0.0,
    #       ...
    #      }]
    #   },
    #   {....}
    # ]

    EMPTY_BOON_MAP = {k: 0 for k in BOON_IDS.keys()}
    df = pd.concat(
        [
            df[column_name_in]  # type: ignore
            .map(  # type: ignore
                lambda cell_value: (
                    EMPTY_BOON_MAP
                    if not isinstance(cell_value, List)
                    else EMPTY_BOON_MAP
                    | {
                        e["id"]: e["buffData"][0][selector]
                        for e in cell_value
                        if e["id"] in BOON_IDS.keys()
                    }
                )
            )
            .apply(pd.Series)
            .rename(columns={k: v + column_name_out for k, v in BOON_IDS.items()})
            for column_name_in, column_name_out, selector in zip(
                _BOON_CATEGORIES_IN,
                BOON_CATEGORIES_OUT,
                _BOON_SELECTORS,
            )
        ]
        + [df.drop(columns=_BOON_CATEGORIES_IN)],
        axis=1,
    )

    filtered_buffs = [
        9283,  # Reinforced armor
        46587,  # Malnourished
        46668,  # Diminished
    ]
    df["Bufffood (uptime%)"] = 0
    if "consumables" in df.columns:
        df["consumables"] = df["consumables"].map(
            lambda cell_value: (
                [e["duration"] for e in cell_value if e["id"] not in filtered_buffs]
                if hasattr(cell_value, "__len__")
                else []
            )
        )
        df["Bufffood (uptime%)"] = (
            df["consumables"]
            .map(lambda e: e[0] if len(e) > 0 else 0)
            .div(1000)
            .div(df["activeTimes"])
            .clip(0, 1)
            + df["consumables"]
            .map(lambda e: e[1] if len(e) > 1 else 0)
            .div(1000)
            .div(df["activeTimes"])
            .clip(0, 1)
        ).div(2)
        df = df.drop(columns=["consumables"])

    if "extHealingStats" in df.columns:
        df["downedHealing"] = df["extHealingStats"].apply(
            lambda x: x["outgoingHealing"][0]["downedHps"]
        )
        df["healing"] = (
            df["extHealingStats"].apply(lambda x: x["outgoingHealing"][0]["hps"])
            - df["downedHealing"]
        )
        df = df.drop(columns="extHealingStats")
    if "extBarrierStats" in df.columns:
        df["barrier"] = df["extBarrierStats"].apply(
            lambda x: x["outgoingBarrier"][0]["bps"]
        )
        df = df.drop(columns="extBarrierStats")

    # filter useless columns
    df = df.drop(columns=_DROP_KEYS, errors="ignore")

    # add some helper columns
    df["spec_color"] = df["profession"].apply(lambda spec: spec_color_map[spec])
    df["profession+name"] = df["profession"].apply(lambda s: s + " | ") + df["name"]

    # cleanup data
    # skillCastUptime does not exist in older versions
    # Also some of the values in skillCastUptime are clearly wrong
    df["distToCom"] = df["distToCom"].clip(0, 1500)
    # XXX stackDist is sometimes NaN? Check again in the future...
    # if df["stackDist"].dtype != np.float64:
    #    df["stackDist"] = df["stackDist"].clip(-5, 2500)
    if "skillCastUptime" in df:
        df["skillCastUptime"] = df["skillCastUptime"].clip(5, 95)
    if "skillCastUptimeNoAA" in df:
        df["skillCastUptimeNoAA"] = df["skillCastUptimeNoAA"].clip(5, 95)

    # absolute values are way less accurate than values per second, so transform some of them
    for key in _DIVIDE_BY_TIME_KEYS:
        if key not in df:
            continue
        df[key] = df[key] / df["activeTimes"]
    for key in BOON_KEYS:
        df[key] = df[key] / df["activeTimes"]
        if "uptime" in key:
            df[key] = df[key].clip(0, 1)

    # add "percentage alive" as it is more understandable than "activeTimes" and fix the "duration" for that
    df["duration"] = pd.to_timedelta(df["duration"]).dt.total_seconds()  # type: ignore
    df["percentageAlive"] = df["activeTimes"] / df["duration"]

    # fix datetime columns
    for key in ["timeStart", "timeEnd"]:
        df[key] = pd.to_datetime(
            df[key].apply(lambda t: t[:-4]), format="%Y-%m-%d %H:%M:%S"
        ) + pd.Timedelta(hours=5)

    # remove keys that were only needed for calculations
    df = df.drop(columns=_INTERMEDIATE_KEYS, errors="ignore")

    # rename for better UX
    df.rename(columns=RENAMED_KEYS, inplace=True)
    return df


def strip_log_data(log):
    if "WvW" not in log["fightName"] and "World vs World" not in log["fightName"]:
        raise FightInvalidException(f"Log is not a WvW fight ({log['fightName']=})")
    for key in list(log.keys()):
        if key not in _RELEVANT_KEYS_DATA:
            del log[key]
    for player in log["players"]:
        for key in list(player.keys()):
            if key not in _RELEVANT_KEYS_DATA_PLAYERS:
                del player[key]
    return log
