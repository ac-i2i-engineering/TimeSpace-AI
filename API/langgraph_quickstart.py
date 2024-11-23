from typing import Annotated
from typing_extensions import TypedDict
from gcal_service import GoogleCalendarService

from pprint import pprint
import os
import webbrowser
import datetime
import pytz
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

load_dotenv()

calendar_service = GoogleCalendarService()
service = calendar_service.service

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")


class State(TypedDict):
   # Messages have the type "list". The `add_messages` function
   # in the annotation defines how this state key should be updated
   # (in this case, it appends messages to the list, rather than overwriting them)
   messages: Annotated[list, add_messages]

class EventTime(BaseModel):
   """Structure for the time properties of the event body"""

   dateTime: str = Field(..., description="DateTime in ISO 8601 format")
   timeZone: str = Field(..., description="Time zone for the event")


class EventBody(BaseModel):
   """Event body for Google Calendar event"""

   summary: str = Field(description="Title of the event")
   start: EventTime = Field(..., description="Start time of the event")
   end: EventTime = Field(..., description="End time of the event")

@tool(args_schema=EventBody, parse_docstring=True)
def add_event(
   summary: str,
   start: EventTime,
   end: EventTime):
   """Method to insert event into Google Calendar using API.Method to insert event into Google Calendar using API.
    The args must follow this exact structure:
    {
        "summary": "Meeting with John",
        "start": {
            "dateTime": "2024-03-20T14:00:00",
            "timeZone": "America/New_York"
        },
        "end": {
            "dateTime": "2024-03-20T15:00:00",
            "timeZone": "America/New_York"
        }
    }"""
   try:
      event_body = EventBody(summary=summary, start=start, end=end).model_dump()
      event = service.events().insert(calendarId='primary', body=event_body).execute()  # Insert event
      print('Event created: ', event_body)
      webbrowser.open(event.get('htmlLink'))  # Open event in Google Calendar UI
   except Exception as e:
      print(f"""{e}\nUnexpected input format: {event_body}""")

prompt = """
   You are the Event Initializer agent for a time management AI figure called Indigo. 
   You will take input detailing an event to insert, and make the appropriate call to `add_event`.
   The correct format will contain:
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
   Output a message detailing how you found this task.
   For now, even if appropriate information is missing, fill it in to the best of your abilities.
   For context, right now the time is {} in {} timezone.
""" # then make a circular chain based on whether questions are answered.

tools = [add_event]
tool_node = ToolNode(tools)

llm = ChatGoogleGenerativeAI(
   model="gemini-1.5-pro", 
   google_api_key=GOOGLE_API_KEY,
   temperature=0.5,
   top_p=0.95,
   top_k=64,
   max_output_tokens=8192,
).bind_tools(tools)

graph_builder = StateGraph(State)


def event_init_AI(state: State):

   current_time = datetime.datetime.now().isoformat() 
   user_timezone = pytz.timezone(pytz.country_timezones('US')[0])

   message = llm.invoke(
      [SystemMessage(content=prompt.format(current_time, user_timezone))] + state["messages"]
   )
   return {"messages": message} # return new 'messages' from invokation of llm on current 'messages' stored in state. Then our add_messages function automically appends



graph_builder.add_node("event_init", event_init_AI)
graph_builder.add_node("process_response", tool_node)
graph_builder.add_edge(START, "event_init")
graph_builder.add_edge("event_init", "process_response")
graph_builder.add_edge("process_response", END)

graph = graph_builder.compile()

output = graph.invoke({"messages": [("user", "Create a meeting with Mark at 5pm.")]})


pprint(output)