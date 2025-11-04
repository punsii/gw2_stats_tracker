import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from filter_logs import _HIDDEN_KEYS
from process_logs import BOON_CATEGORIES_OUT, BOON_IDS


def render_stat_comparison(df, groups, group_means, filters):
    format = "%d.%m.%y %H:%M"
    time_range_string = (
        "("
        + pd.Timestamp(filters.start_time_min).strftime(format)
        + " - "
        + pd.Timestamp(filters.start_time_max).strftime(format)
        + ")"
    )

    stat_selector: str = ""
    if filters.stat_category == "Boons":
        boon = st.selectbox("Boon:", options=sorted(BOON_IDS.values()))
        boon_type = st.selectbox("Boon Type:", options=BOON_CATEGORIES_OUT)
        stat_selector = boon + boon_type  # type: ignore
    else:
        key_selection = [key for key in list(df) if key not in _HIDDEN_KEYS]
        stat_selector = st.selectbox(
            "Select Stats",
            key_selection,
            help="Choose the data that you are interested in.",
        )

    # violoin plot
    fig = go.Figure()
    try:
        # XXX needs a `sorted_by` classification for the `stat_selector`
        # sorted_keys = mean[stat_selector].sort_values().tail(30)
        sorted_keys = group_means[stat_selector].sort_values()
    except KeyError:
        st.write("")
        st.write("Nothing to see here ...")
        st.stop()

    for group in sorted_keys.index:
        marker = {
            "color": groups.get_group(group)["spec_color"].value_counts().idxmax(),
        }
        if stat_selector in ["Time Alive (%)", "Bufffood (uptime%)"]:
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
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "toImageButtonOptions": {
                "format": "png",
                "filename": f"{stat_selector.split("(")[0].replace(' ', '').lower()}",
            },
        },
    )

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
        df.groupby(filters.group_by)[stat_selector]
        .rolling(rolling_average_window, win_type="triang")
        .mean()
        .reset_index(0, drop=True)
    )
    fig = go.Figure()
    for group in sorted_keys.index:
        marker = {
            "color": groups.get_group(group)["spec_color"].value_counts().idxmax()
        }
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
