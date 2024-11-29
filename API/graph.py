from datatypes import State
from tools import tool_node
from langgraph_quickstart import events_initializer
from event_lookup import event_lookup_main

from langgraph.graph import StateGraph, START, END

# Initialize graph
graph_builder = StateGraph(State)

# Add nodes (currently just event_lookup --> tool_node for testing)

#graph_builder.add_node("event_init", events_initializer)
graph_builder.add_node("event_lookup", event_lookup_main)
graph_builder.add_node("process_response", tool_node)

# Add edges 
graph_builder.add_edge(START, "event_lookup")
graph_builder.add_edge("event_lookup", "process_response")
graph_builder.add_edge("process_response", END)

graph = graph_builder.compile()

def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        questions = s["questions"]
        if isinstance(message, tuple):
            print(message)
            print(questions)
        else:
            message.pretty_print()
            print(questions)

# Invoke graph on sample input
print_stream(
    graph.stream(
        {"messages": [("user", "Team lunch")]},
        stream_mode="values"
    )
)