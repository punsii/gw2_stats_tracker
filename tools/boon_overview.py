import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from color_lib import spec_color_map
from process_logs import BOON_IDS


def render_boon_overview(groups, group_means, filters):
    format = "%d.%m.%y %H:%M"
    time_range_string = (
        "("
        + pd.Timestamp(filters.start_time_min).strftime(format)
        + " - "
        + pd.Timestamp(filters.start_time_max).strftime(format)
        + ")"
    )

    # bar chart
    boons_selectors = [boon + " (Group Generation/s)" for boon in BOON_IDS.values()]

    boon_means = group_means[boons_selectors]
    normalized_means = boon_means / boon_means.max()
    # if you want the absolute values
    # normalized_means = boon_means

    fig = go.Figure()
    spec_order = [s for s in spec_color_map.keys() if s in normalized_means.index]
    for idx in spec_order:
        row = normalized_means.loc[idx]
        color = groups.get_group(idx)["spec_color"].value_counts().idxmax()
        fig.add_trace(
            go.Bar(
                name=str(idx),
                x=boon_means.columns,  # x needs the boon names (columns)
                y=row.values,  # numeric values (call or use .values)
                marker=dict(color=color),
            )
        )

    fig.update_layout(
        barmode="stack",
        title=f"Group Boon Generation {time_range_string}",
        title_x=0.5,
        xaxis_title="Boon",
        yaxis_title="Normalized Generation",
    )
    st.write(fig)

    fig = go.Figure()
    for idx in spec_order:
        row = normalized_means.loc[idx]
        marker = {
            "color": groups.get_group(idx)["spec_color"].value_counts().idxmax(),
        }
        fig.add_trace(
            go.Scatterpolar(
                r=row.to_list(),
                theta=boons_selectors,
                fill="toself",
                name=idx,
                marker=marker,
            )
        )
    fig.update_layout(
        title=f"Group Boon Generation {time_range_string}",
        title_x=0.5,
        template="plotly_dark",
    )
    st.write(fig)
