import logging
import os

import streamlit as st

from fetch_logs import fetch_data
from filter_logs import filter_data, get_inputs
from tools.boon_overview import render_boon_overview
from tools.stat_comparison import render_stat_comparison

logging.basicConfig(filename="myapp.log", level=logging.INFO)
st.set_page_config(layout="wide")
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

TOOLS = [
    "Stat comparison",
    "Boon overview",
]
tool_selector = st.sidebar.selectbox("Tool selection:", options=TOOLS)


if not userToken:
    st.stop()

df = fetch_data(userToken)  # type: ignore
filters = get_inputs(df, tool_selector)
df = filter_data(df, filters)
groups = df.groupby(filters.group_by)
group_means = groups.mean(numeric_only=True)

DEBUG = st.sidebar.checkbox("Show debug data")
if DEBUG:
    st.write(f"Filtered absolute data: {df.shape}:", df)
    st.write(f"Filtered averaged data: {group_means.shape}:", group_means)

if tool_selector == "Stat comparison":
    render_stat_comparison(df, groups, group_means, filters)
elif tool_selector == "Boon overview":
    render_boon_overview(groups, group_means, filters)
