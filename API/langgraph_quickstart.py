from typing import Annotated

from typing_extensions import TypedDict
import os
import textwrap
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
   model="gemini-1.5-pro", 
   google_api_key=GOOGLE_API_KEY,
   temperature=1,
   top_p=0.95,
   top_k=64,
   max_output_tokens=8192,
   response_mime_type="application/json"
)

messages = [
   ("system", textwrap.dedent(f"""
                You are a calendar assistant. Based on the following input, generate the required JSON for a Google Calendar event.
                The JSON should contain:
                - "summary": a short title for the event,
                - "start": the start time in ISO 8601 format,
                - "end": the end time in ISO 8601 format,
                - "timeZone": the time zone for the event.
                An example format is this:
                {{
                    'summary': 'Meeting with John',
                    'start': {{
                        'dateTime': '2024-10-18T10:00:00',
                        'timeZone': 'America/New_York',
                    }},
                    'end': {{
                        'dateTime': '2024-10-18T11:00:00',
                        'timeZone': 'America/New_York',
                    }},
                }}
            """)),
   ("human", "Create a meeting at 2pm with John")
]

print(llm.invoke(messages))

""" class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)



llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")


def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()

from IPython.display import Image, display

try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception:
    # This requires some extra dependencies and is optional
    pass """