from dataclasses import dataclass
from typing import List

import pandas as pd
import streamlit as st
from pandas.core.dtypes.dtypes import date

from process_logs import BOON_KEYS, RENAMED_KEYS


@dataclass
class InputParams:
    stat_category: str
    group_by: str

    account_name_filter: List[str]
    character_name_filter: List[str]
    profession_filter: List[str]

    dates: List[date]
    start_time_min: date
    start_time_max: date


# These keys are needed but should not be selectable
_HIDDEN_KEYS = [
    "id",
    "timeStart",
    "profession",
    "name",
    "profession+name",
    "spec_color",
    "account",
]

_KEY_CATEGORIES = {
    "Default": [
        RENAMED_KEYS["dps"],
        RENAMED_KEYS["downContribution"],
        RENAMED_KEYS["healing"],
        RENAMED_KEYS["barrier"],
        RENAMED_KEYS["boonStrips"],
        RENAMED_KEYS["boonStripDownContribution"],
        RENAMED_KEYS["appliedCrowdControl"],
        RENAMED_KEYS["appliedCrowdControlDownContribution"],
        RENAMED_KEYS["condiCleanse"],
        RENAMED_KEYS["avgActiveBoons"],
        RENAMED_KEYS["avgActiveConditions"],
        RENAMED_KEYS["distToCom"],
        RENAMED_KEYS["swapCount"],
        RENAMED_KEYS["skillCastUptime"],
        RENAMED_KEYS["percentageAlive"],
    ],
    "Offense": [
        RENAMED_KEYS["dps"],
        RENAMED_KEYS["downContribution"],
        RENAMED_KEYS["condiDps"],
        RENAMED_KEYS["powerDps"],
        RENAMED_KEYS["criticalDmg"],
        RENAMED_KEYS["boonStrips"],
        RENAMED_KEYS["boonStripDownContribution"],
        RENAMED_KEYS["killed"],
        RENAMED_KEYS["downed"],
        RENAMED_KEYS["interrupts"],
        RENAMED_KEYS["appliedCrowdControl"],
        RENAMED_KEYS["appliedCrowdControlDownContribution"],
        RENAMED_KEYS["appliedCrowdControlDuration"],
        RENAMED_KEYS["appliedCrowdControlDurationDownContribution"],
        RENAMED_KEYS["missed"],
        RENAMED_KEYS["criticalRate"],
        RENAMED_KEYS["glanceRate"],
        RENAMED_KEYS["flankingRate"],
    ],
    "Defense": [
        RENAMED_KEYS["healing"],
        RENAMED_KEYS["barrier"],
        RENAMED_KEYS["downedHealing"],
        RENAMED_KEYS["resurrects"],
        RENAMED_KEYS["resurrectTime"],
        RENAMED_KEYS["condiCleanse"],
        RENAMED_KEYS["condiCleanseSelf"],
        RENAMED_KEYS["stunBreak"],
        RENAMED_KEYS["removedStunDuration"],
        RENAMED_KEYS["evaded"],
        RENAMED_KEYS["blocked"],
        RENAMED_KEYS["invulned"],
    ],
    # These are keys that someone might be intetested in
    # but which just clutter the application most of the time.
    "Miscellaneous": [
        RENAMED_KEYS["distToCom"],
        RENAMED_KEYS["skillCastUptime"],
        RENAMED_KEYS["skillCastUptimeNoAA"],  # --> 'skillCastUptime' should be enough
        RENAMED_KEYS["swapCount"],
        RENAMED_KEYS["totalDamageCount"],  # --> 'dps' should be enough
        RENAMED_KEYS["removedStunDuration"],
        # RENAMED_KEYS["boonStripDownContributionTime"],
        RENAMED_KEYS["appliedCrowdControlDuration"],
        RENAMED_KEYS["appliedCrowdControlDurationDownContribution"],
    ],
    "Unlabeled": [],
}


def get_inputs(df: pd.DataFrame, tool_selector: str) -> InputParams:
    stat_category_help = """
    Select which stats you are interested in:

    Default:
      Stats that are usually helpfull.

    Offense:
      Offensive stats (Damage, Boons strips, etc..)

    Defense:
      Defensive stats (Healing, Condition Cleanses, etc..)

    Boons:
      Boon generation.

    Miscellaneous:
      Most values reported by ArcDps are either useless or it is unclear what they
      mean. Select this category if you want to browse through them anyway.

    Unlabeled:
      New datapoints are added to the processed ardps logs from time to time.
      If I did not have time to classify them and clean them up they will first appear here.
    """
    STAT_CATEGORIES = [
        "Default",
        "Offense",
        "Defense",
        "Boons",
        "Miscellaneous",
        "Unlabeled",
    ]

    stat_category = "Boons"
    group_by_selection = "profession"
    if tool_selector != "Boon overview":
        stat_category = st.sidebar.selectbox(
            "Stat selection:", options=STAT_CATEGORIES, help=stat_category_help
        )
        group_by_selection = st.sidebar.selectbox(
            "Group by:",
            [
                "character name",
                "character name & profession",
                "profession",
                "account name",
            ],
        )
    match group_by_selection:
        case "profession":
            group_by = "profession"
        case "character name":
            group_by = "name"
        case "account name":
            group_by = "account"
        case _:
            group_by = "profession+name"

    account_name_filter = st.sidebar.multiselect(
        "Filter Account Names:", sorted(df.account.unique())
    )
    character_name_filter = st.sidebar.multiselect(
        "Filter Character Names:", sorted(df.name.unique())
    )
    profession_filter = st.sidebar.multiselect(
        "Filter Professions:", sorted(df.profession.unique())
    )

    dates: List[date] = df["timeStart"].unique()
    format = "%d.%m. %H:%M"
    start_time_min: date = st.sidebar.select_slider(
        "First + Last Date:",
        format_func=lambda t: pd.Timestamp(t).strftime(format),
        options=dates,
        value=dates.min(),
    )
    start_time_max: date = st.sidebar.select_slider(
        "hidden",
        label_visibility="collapsed",
        format_func=lambda t: pd.Timestamp(t).strftime(format),
        options=dates,
        value=dates.max(),
    )
    if start_time_min > start_time_max:
        st.sidebar.error("First Date must be before Last Date")
        st.stop()

    return InputParams(
        stat_category,
        group_by,
        account_name_filter,
        character_name_filter,
        profession_filter,
        dates,
        start_time_min,
        start_time_max,
    )


@st.cache_data(max_entries=500, show_spinner=False, persist=True)
def filter_data(df: pd.DataFrame, filters: InputParams):
    df = df[df["timeStart"].between(filters.start_time_min, filters.start_time_max)]
    if filters.character_name_filter:
        df = df[df["name"].isin(filters.character_name_filter)]
    if filters.account_name_filter:
        df = df[df["account"].isin(filters.account_name_filter)]
    if filters.profession_filter:
        df = df[df["profession"].isin(filters.profession_filter)]

    # create inputs
    unlabeled_keys = [
        key
        for key in list(df)
        if key not in _HIDDEN_KEYS
        and key not in _KEY_CATEGORIES["Default"]
        and key not in _KEY_CATEGORIES["Offense"]
        and key not in _KEY_CATEGORIES["Defense"]
        and key not in BOON_KEYS
        and key not in _KEY_CATEGORIES["Miscellaneous"]
    ]

    result_keys = _HIDDEN_KEYS.copy()
    match filters.stat_category:
        case "Default":
            result_keys += _KEY_CATEGORIES["Default"]
        case "Offense":
            result_keys += _KEY_CATEGORIES["Offense"]
        case "Defense":
            result_keys += _KEY_CATEGORIES["Defense"]
        case "Boons":
            result_keys += BOON_KEYS
        case "Miscellaneous":
            result_keys += _KEY_CATEGORIES["Miscellaneous"]
        case "Unlabeled":
            result_keys += unlabeled_keys

    return df[result_keys]
