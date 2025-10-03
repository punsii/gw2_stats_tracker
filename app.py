import logging
import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from fetch_logs import _HIDDEN_KEYS, fetch_data
from process_logs import BOON_CATEGORIES_OUT, BOON_IDS

logging.basicConfig(filename="myapp.log", level=logging.INFO)
# Inject css to increase the default sidebar size
st.markdown(
    """
   <style>
   [data-testid="stSidebar"][aria-expanded="true"]{
       min-width: 375px;
   }
   """,
    unsafe_allow_html=True,
)


# parse userTokens from env
userTokens = {"Custom": ""}
if "DPS_REPORT_TOKENS" in os.environ:
    for token in os.environ["DPS_REPORT_TOKENS"].split(","):
        name, value = token.split(":")
        userTokens |= {name: value.strip()}


# fetch data
token_help = """
# PROTECT YOUR USER TOKEN! Treat it like a password.
Anyone with access to this value can look up any logs uploaded with it.

If you select 'Custom', you will be able to use your own userToken.
If other values can be selected they were added by the person hosting this application.
Talk to them if you want to know their values.

ArcDps logs that were uploaded with the selected userToken will be displayed here.
In order to upload logs with the correct userToken you can use the [PlenBotLogUploader](https://plenbot.net/uploader/) (recommended)
or the [Arcdps-Uploader Extension](https://github.com/nbarrios/arcdps-uploader) (less well maintained).

See the relevant documentation [here](https://dps.report/api).
"""

userToken = None
userTokenName = st.sidebar.selectbox(
    "dps.report userToken:", options=userTokens.keys(), help=token_help
)
if userTokenName == "Custom":
    userToken = st.sidebar.text_input("custom token", label_visibility="collapsed")
else:
    userToken = userTokens[userTokenName]

stat_category_help = """
Select which stats you are interested in:

Default:
  Stats that are usually helpfull.

Boons:
  Boon generation.

Miscellaneous:
  Most values reported by ArcDps are either useless or it is unclear what they
  mean. Select this category if you want to browse through them anyway.
"""
STAT_CATEGORIES = ["Default", "Boons", "Miscellaneous"]
stat_category = st.sidebar.selectbox(
    "Stat selection:", options=STAT_CATEGORIES, help=stat_category_help
)


if not userToken:
    st.stop()

df = fetch_data(userToken, stat_category)  # type: ignore
stat_selector = ""
if stat_category == "Boons":
    boon = st.sidebar.selectbox(
        "Boon:", options=sorted(BOON_IDS.values()), help=stat_category_help
    )
    boon_type = st.sidebar.selectbox(
        "Boon Type:", options=BOON_CATEGORIES_OUT, help=stat_category_help
    )
    stat_selector = boon + boon_type  # type: ignore
else:
    key_selection = [key for key in list(df) if key not in _HIDDEN_KEYS]
    stat_selector = st.sidebar.selectbox(
        "Select Stats",
        key_selection,
        help="Choose the data that you are interested in.",
    )

group_by_selection = st.sidebar.selectbox(
    "Group by:",
    ["character name", "character name & profession", "profession", "account name"],
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
dates = df["timeStart"].unique()
format = "%d.%m. %H:%M"
start_time_min = st.sidebar.select_slider(
    "First + Last Date:",
    format_func=lambda t: pd.Timestamp(t).strftime(format),
    options=dates,
    value=dates.min(),
)
start_time_max = st.sidebar.select_slider(
    "hidden",
    label_visibility="collapsed",
    format_func=lambda t: pd.Timestamp(t).strftime(format),
    options=dates,
    value=dates.max(),
)
if start_time_min > start_time_max:
    st.sidebar.error("First Date must be before Last Date")
    st.stop()

format = "%d.%m.%y %H:%M"
time_range_string = (
    "("
    + pd.Timestamp(start_time_min).strftime(format)
    + " - "
    + pd.Timestamp(start_time_max).strftime(format)
    + ")"
)


# apply filters
df = df[df["timeStart"].between(start_time_min, start_time_max)]
if character_name_filter:
    df = df[df["name"].isin(character_name_filter)]
if account_name_filter:
    df = df[df["account"].isin(account_name_filter)]
if profession_filter:
    df = df[df["profession"].isin(profession_filter)]


if st.checkbox("Show raw data"):
    f"df (filtered) {df.shape}:", df


groups = df.groupby(group_by)
mean = groups.mean(numeric_only=True)
if st.checkbox("Show averaged data"):
    f"df (filtered) {mean.shape}:", mean


# violoin plot
fig = go.Figure()
sorted_keys = mean[stat_selector].sort_values()
for group in sorted_keys.index:
    marker = {
        "color": groups.get_group(group)["spec_color"].value_counts().idxmax(),
    }
    if stat_selector in ["TimeAlive(%)", "Bufffood(uptime%)"]:
        fig.add_trace(
            go.Bar(
                marker=marker,
                name=group,
                y=[sorted_keys[group]],
                x=[group],
            )
        )
    else:
        fig.add_trace(
            go.Violin(
                jitter=1,
                marker=marker,
                meanline_visible=True,
                name=group,
                pointpos=0,
                points="all",
                spanmode="hard",
                y=groups.get_group(group)[stat_selector],
            )
        )

fig.update_layout(
    title=f"{stat_selector}  {time_range_string}",
    title_x=0.5,
    legend_traceorder="reversed",
)
st.write(fig)

# rolling average
rolling_average_help = """
The plot below shows how the selected metric has changed over time.
This slider causes the data to be averaged over N fights instead of
displaying each data point individually. Choose higher values for
metrics that vary wildly from fight to fight.
"""
rolling_average_window = st.slider(
    "Rolling Avgerage Window Size:", 1, 25, 5, help=rolling_average_help
)
df["rolling_average"] = (
    df.groupby(group_by)[stat_selector]
    .rolling(rolling_average_window, win_type="triang")
    .mean()
    .reset_index(0, drop=True)
)
fig = go.Figure()
for group in sorted_keys.index:
    marker = {"color": groups.get_group(group)["spec_color"].value_counts().idxmax()}
    fig.add_trace(
        go.Scatter(
            marker=marker,
            mode="markers+lines",
            name=group,
            x=groups.get_group(group)["timeStart"],
            y=groups.get_group(group)["rolling_average"],
        )
    )
fig.update_layout(title=stat_selector, title_x=0.5, legend_traceorder="reversed")
fig.layout = {"xaxis": {"type": "category", "categoryorder": "category ascending"}}
st.write(fig)
