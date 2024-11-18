from typing import Annotated, Optional
from typing_extensions import TypedDict

from pydantic import BaseModel, Field

import os
import textwrap
import json
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage

load_dotenv()

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]



# Insert new event into Google Calendar
def add_event(self, event_body):
   try:
      if self.validate_event_body(event_body):
            event = self.service.events().insert(calendarId='primary', body=event_body).execute()  # Insert event
            print('Event created: ', event_body)
            webbrowser.open(event.get('htmlLink'))  # Open event in Google Calendar UI
   except Exception as e:
      print(
            textwrap.dedent(f"""
               {e}
               Unexpected input format: {event_body}
            """)
      )

# Handle response from AI
def process_response(state: State):
   try:
      message = state["messages"][-1].content
      event_body = json.loads(message)
      add_event(event_body)
   except Exception as e:
      print(
            textwrap.dedent(f"""
               {e}
               Unexpected response format: {message}
            """)
      )


# Helper method to validate event specifications
# Needs work, doesn't give useful output or check type of input, also KeyError doesn't work as a catch all
def validate_event_body(self, event_body):
   try:
      return event_body['summary'] and event_body['start'] and event_body['end']
   except Exception as e:
      return False

prompt = textwrap.dedent(f"""
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
            """)

llm = ChatGoogleGenerativeAI(
   model="gemini-1.5-pro", 
   google_api_key=GOOGLE_API_KEY,
   temperature=1,
   top_p=0.95,
   top_k=64,
   max_output_tokens=8192,
)# .bind_tools([process_response])


class EventTime(BaseModel):
    dateTime: str = Field(..., description="DateTime in ISO 8601 format")
    timeZone: str = Field(..., description="Time zone for the event")


class EventBody(BaseModel):
   """Event body for Google Calendar event"""

   summary: str = Field(description="Title of the event")
   start: EventTime
   end: EventTime


structured_llm = llm.with_structured_output(EventTime)

graph_builder = StateGraph(State)


def event_init_AI(state: State):
   return {"messages": [structured_llm.invoke([SystemMessage(content=prompt)] + state["messages"])]} # return new 'messages' from invokation of llm on current 'messages' stored in state. Then our add_messages function automically appends


graph_builder.add_node("event_init", event_init_AI)
graph_builder.add_node("process_response", process_response)
graph_builder.add_edge(START, "event_init")
graph_builder.add_edge("event_init", "process_response")
graph_builder.add_edge("process_response", END)

graph = graph_builder.compile()

output = graph.invoke({"messages": [("user", "Create a meeting with John at 2pm.")]})


print(output)