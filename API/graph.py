from datatypes import State
from tools import tool_node
from langgraph_quickstart import events_initializer
from event_lookup import event_lookup_main, event_lookup_query, event_lookup_select

from langgraph.graph import StateGraph, START, END

# Initialize graph
graph_builder = StateGraph(State)

# Add nodes (currently just event_lookup flow for testing)

#graph_builder.add_node("main", event_lookup_main)
graph_builder.add_node("tool", tool_node)
graph_builder.add_node("query", event_lookup_query)
graph_builder.add_node("select", event_lookup_select)

# Add edges 
graph_builder.add_edge(START, "query")
""" graph_builder.add_conditional_edges(
    "main",
    lambda state: "query" if state["questions"].query == "unknown" else "select" if state["questions"].selection == "unknown" else END
) """
graph_builder.add_edge("query", "tool")
graph_builder.add_edge("tool", "select")
#graph_builder.add_edge("select", "main")

graph = graph_builder.compile()

def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        questions = s["questions"] or "nothing"
        if isinstance(message, tuple):
            print(message)
            print(questions)
        else:
            message.pretty_print()
            print("Questions:", questions)
        print()

# Invoke graph on sample input
print_stream(
    graph.stream(
        {"messages": [("user", "Cancel all my meetings for the next 57 hours")], "questions": None},
        stream_mode="values"
    )
)

# Right now we specifically route to certain nodes to answer certain questions, but require routing back to some supervisor to fill in the answer
# That's not necessarily bad but it might be better to think about some way to more directly tie results from other agents back to the questions they were called on to answer