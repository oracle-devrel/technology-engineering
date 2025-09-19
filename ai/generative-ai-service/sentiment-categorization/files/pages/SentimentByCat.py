import json

import pandas as pd
import streamlit as st
import plotly.express as px

from backend.feedback_wrapper import FeedbackAgentWrapper


# Function to generate Graphviz flowchart with rounded boxes
def create_flowchart(nodes, edges, highlight_node=None, highlight_edge=None, label=""):
    dot = "digraph G {\n"
    fontname = "Courier New"
    dot += f'    graph [fontname="{fontname}"];\n'

    # Define nodes with rounded style
    for step in nodes:
        node_color = "paleturquoise" if step != highlight_node else "gold"
        dot += f'    "{step}" [shape=box, style="rounded,filled", fillcolor={node_color}, color=dimgrey, fontname="{fontname}", fontsize=12, fontcolor=dimgrey];\n'

    # Define edges with conditional highlighting
    for source, target in edges:
        edge_color = "dimgrey" if (source, target) != highlight_edge else "gold"
        dot += f'    "{source}" -> "{target}" [label="{label}", color={edge_color}, penwidth=1.5, arrowsize=0.7];\n'

    dot += "}\n"
    return dot


def find_result(data):
    target_key = "reports"
    for value_list in data.values():  # All lists
        for subdict in value_list:  # All dictionaries inside lists
            if isinstance(subdict, dict):  # Ensure it is a dict
                for subvalue in subdict.values():  # Look for internal values
                    if isinstance(subvalue, dict) and target_key in subvalue:
                        return subvalue[target_key]
    return None


# Function to execute the flow dynamically
def execute_flow(col1, col2):
    competitor_report = FeedbackAgentWrapper()
    steps, edges = competitor_report.get_nodes_edges()

    i = 0
    current_step = steps[0]

    step_outputs = {step: [{}] for step in steps}

    # Store active step for highlight
    if "active_step" not in st.session_state:
        st.session_state.active_step = steps[0]

    with col1:
        flowchart_placeholder = st.empty()
        flowchart_dot = create_flowchart(
            steps, edges, highlight_node=current_step, highlight_edge=edges[0]
        )
        flowchart_placeholder.graphviz_chart(flowchart_dot)

    with col2:
        tab_objects = st.tabs(steps[1:-1])

    while current_step != steps[-1]:
        with col1:
            with st.spinner("Wait for it...", show_time=True):
                next_step, output = competitor_report.run_step_by_step()
                update_tab = True
                if not output:
                    next_step = steps[-1]
                    update_tab = False
                else:
                    # Store the output in the dictionary
                    step_outputs[current_step].append(output)

                if update_tab:
                    idx = steps.index(next_step) - 1
                    with col2:
                        with tab_objects[idx]:
                            my_tab = st.container(height=550, border=False)
                            with my_tab:
                                st.json(
                                    output, expanded=4
                                )  # Display result inside respective tab

                # Determine the next step & edge
                current_edge = (current_step, next_step) if next_step else None

                # Update flowchart highlighting current step
                with col1:
                    flowchart_dot = create_flowchart(
                        steps,
                        edges,
                        highlight_node=next_step,
                        highlight_edge=current_edge,
                    )
                    flowchart_placeholder.graphviz_chart(flowchart_dot)

                current_step = next_step
                i += 1

    st.session_state.flow_completed = True  # Mark execution as completed

    return step_outputs


def display_category(data):
    # Iterate over categories
    for category in data["categories"]:
        with st.container():
            st.subheader(f"📌 {category['category_level_1']}")
            st.write(category["summary"])

            # Sentiment Scores
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "📊 Avg Sentiment Score",
                    category["average_sentiment_score"],
                    delta=None,
                )
                st.progress(
                    category["average_sentiment_score"] / 5
                )  # Normalize to range 0-1
            with col2:
                st.success(
                    f"💚 Highest Sentiment: {category['highest_sentiment_message']['sentiment_score']}"
                )
                st.write(f"**{category['highest_sentiment_message']['summary']}**")
            with col3:
                st.error(
                    f"❌ Lowest Sentiment: {category['lowest_sentiment_message']['sentiment_score']}"
                )
                st.write(f"**{category['lowest_sentiment_message']['summary']}**")

            # Key Insights
            st.markdown("### 🔍 Key Insights")
            for insight in category["key_insights"]:
                st.info(f"📌 {insight}")

            # Subcategories
            st.markdown("### 📂 Subcategories Breakdown")
            for subcategory in category["subcategories"]:
                with st.expander(
                    f"📎 {subcategory['category_level_2']} (Avg Sentiment: {subcategory['average_sentiment_score']})"
                ):
                    st.write(subcategory["summary"])

                    # Sentiment Range Bar
                    sentiment_df = pd.DataFrame(
                        {
                            "Sentiment Score": ["Lowest", "Highest"],
                            "Value": [
                                subcategory["sentiment_range"]["lowest"],
                                subcategory["sentiment_range"]["highest"],
                            ],
                        }
                    )
                    st.bar_chart(sentiment_df.set_index("Sentiment Score"))

                    # Notable Trends
                    st.markdown("**📉 Notable Sentiment Trends:**")
                    for trend in subcategory["notable_sentiment_trends"]:
                        st.warning(f"🔻 {trend}")


def display_sentiment(steps_data):
    categorize_data = steps_data["summarize"]

    df = pd.DataFrame(categorize_data[1]["categorize"]["categories"])
    df.to_csv("test.csv", index=False)

    st.subheader("📊 Sentiment Analysis by Category")
    fig = px.bar(
        df,
        x="id",
        y="sentiment_score",
        color="sentiment_score",
        text="topic",
        labels={"Message": "Id", "sentiment_score": "Sentiment Score (1-10)"},
        title="Sentiment Scores per Feedback Category",
    )

    fig.update_traces(textposition="inside")
    st.plotly_chart(fig, use_container_width=True)


# Main layout
st.title("📊 Customer Feedback Dashboard")

# Sidebar: Topic text input (disabled during execution)
if "flow_completed" not in st.session_state:
    st.session_state.flow_completed = True  # Start in ready state

start_button = st.sidebar.button(
    "Start!", type="primary", disabled=not st.session_state.flow_completed
)

# Wait for user input before execution starts
if start_button and st.session_state.flow_completed:
    col1, col2 = st.columns([0.4, 0.6], gap="medium")

    st.session_state.flow_completed = False  # Lock input
    step_outputs = execute_flow(col1, col2)
    feedback_result = find_result(step_outputs)

    st.divider()
    categories = json.loads(feedback_result[0])
    display_category(categories)
    st.divider()
    display_sentiment(step_outputs)
