import streamlit as st
from plotly import graph_objects as go

import db

# Configure page.
st.set_page_config(page_title="Tests Data", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# Select which tests to display based on timestamp.
entries = test_data = db.Test.objects()
timestamps = sorted(set([entry.timestamp for entry in entries]), reverse=True)
timestamp = st.sidebar.selectbox("Timestamp", timestamps)

# Select which test to display based on name.
entries = test_data = db.Test.objects(timestamp=timestamp)
tests = sorted(set([entry.name for entry in entries]))
name = st.sidebar.selectbox("Name", tests)

# Divider.
st.sidebar.divider()

# Refresh button.
if st.sidebar.button("Refresh"):
    st.rerun()

# Get test data.
test_data = db.Test.objects(timestamp=timestamp, name=name).first()

# Extract data and format it to be displayed in the graph.
x, y = [], []
for i, _ in enumerate(test_data.states):
    x.append(test_data.times[i])
    y.append(0 if test_data.states[i] == 1 else 1)

    x.append(test_data.times[i])
    y.append(test_data.states[i])

# Create graph.
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=x,
        y=y,
        name="Signal",
        mode="lines",
        line=dict(color="limegreen" if test_data.passed else "orangered"),
        showlegend=False,
        hovertemplate="Time: %{x:.3f}<extra></extra>",
    )
)

# Configure graph layout.
fig.update_layout(
    xaxis=dict(
        title="Time",
        tickmode="linear",
        dtick=1,
        range=[x[0] - 0.1, x[-1] + 0.1],
        showgrid=True,
        showline=True,
    ),
    yaxis=dict(
        title="State",
        range=[-0.1, 1.1],
        dtick=1,
    ),
    width=1400,
    height=400,
)

# Display graph and log.
st.title(f"Test uuid:")
st.text(f"{test_data.uuid}")
st.plotly_chart(fig)
st.text(test_data.log)
