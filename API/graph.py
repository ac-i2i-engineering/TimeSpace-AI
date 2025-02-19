from datatypes import State, Agent
from tools import tools, print_state, print_stream

from event_initializer import EventInitializer
from event_lookup import EventLookup
from event_editor import EventEditor
from indigo import Indigo
from contextualizer import Contextualizer

import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode

load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

class Graph(Agent):
    """Main graph for Indigo, incorporates all agents"""
    def __init__(self):

        # Define LLM for automation agents (low temperature)
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", 
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3
        )

        # Define tool node to be used in various agent flows
        tool_node = ToolNode(tools)
        
        # Initialize low-temp agents
        event_initializer = EventInitializer(llm, tool_node)
        event_lookup = EventLookup(llm, tool_node)
        event_editor = EventEditor(llm, tool_node, event_lookup)
        contextualizer = Contextualizer(llm)

        
        # Define LLM for user-facing agent (high temperature)
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=GOOGLE_API_KEY,
        )
        # Initialize Indigo
        indigo = Indigo(llm)

        
        # Initialize graph
        builder = StateGraph(State)

        # Add all nodes
        builder.add_node("event_lookup", event_lookup)
        builder.add_node("event_editor", event_editor)
        builder.add_node("event_initializer", event_initializer)
        builder.add_node("contextualizer", contextualizer)
        builder.add_node("indigo", indigo)

        # Define flow
        builder.add_conditional_edges(START, lambda state: "indigo" if "context" in state else "contextualizer") # Router determines whether user's use case is covered by a specialized agent
        builder.add_edge("contextualizer", "indigo")
        builder.add_conditional_edges("indigo", lambda state: END if state["helper_agent"] == "none" else state["helper_agent"]) # Flow is routed accordingly

        # All specialized agents route to Indigo for final user-facing output
        builder.add_edge("event_lookup", "indigo")
        builder.add_edge("event_editor", "indigo")
        builder.add_edge("event_initializer", "indigo")


        checkpointer = MemorySaver()
        self.graph = builder.compile(checkpointer=checkpointer)

# TESTING

def main():

    # Define graph and initial state
    graph = Graph()

    state = {
        "messages": [("user", "Hello!")]
    }

    thread = {"configurable": {"thread_id": "1"}}

    stream = graph.stream(state, thread, stream_mode="updates", subgraphs=True)
    print_stream(stream)

    # Input loop for command line testing with Indigo
    while True:
        message = input("Chat with Indigo: ")

        if message == "q":
            break
        
        state["messages"] = [("user", message)]

        stream = graph.stream(state, thread, stream_mode="updates", subgraphs=True)
        print_stream(stream)

if __name__ == "__main__":
    main()