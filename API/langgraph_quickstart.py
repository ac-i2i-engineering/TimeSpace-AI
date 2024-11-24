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
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

service = GoogleCalendarService()

# Define classes for use in tools and graph

class State(TypedDict):
   messages: Annotated[list, add_messages]

class EventBody(BaseModel):
   """Event body for Google Calendar event"""

   summary: str = Field(description="Title of the event", example="Meeting with John")
   startTime: str = Field(..., description="DateTime in ISO 8601 format, starting time of the event", example="2024-10-18T10:00:00")
   endTime: str = Field(..., description="DateTime in ISO 8601 format, endgin time of the event", example="2024-10-18T11:00:00")
   timeZone: str = Field(..., description="Time zone for the event", example="America/New_York")

@tool(args_schema=EventBody)
def add_event(
   summary: str,
   startTime: str,
   endTime: str,
   timeZone: str):
   """Method to insert event into Google Calendar using API."""
   try:
      # Construct event body from args (still unsure about this system, was designed for best AI understanding of args)
      event_body = {
         "summary": summary,
         "start": {
            "dateTime": startTime,
            "timeZone": timeZone
         },
         "end": {
            "dateTime": endTime,
            "timeZone": timeZone
         },
      }
      event = service.events().insert(calendarId='primary', body=event_body).execute()  # Insert event
      #webbrowser.open(event.get('htmlLink')) # Open event in Google Calendar UI
   except Exception as e:
      print(f"""{e}\nUnexpected input format: {event_body}""")


def event_init_AI(state: State):

   current_time = datetime.datetime.now().isoformat() 
   user_timezone = pytz.timezone(pytz.country_timezones('US')[0])

   message = llm.invoke(
      [SystemMessage(content=prompt.format(current_time, user_timezone))] + state["messages"]
   )
   return {"messages": message} # return new 'messages' from invokation of llm on current 'messages' stored in state. Then our add_messages function automically appends


prompt = """
   You are the Event Initializer agent for a time management AI figure called Indigo. 
   You will take input detailing one or more events to insert, and make the appropriate call to `add_event`. For multiple events, simply make multiple calls to `add_event`.
   The appropriate argument format for `add_event` is detailed in its description and argument details.
   Output a content message detailing how you found this task.
   For context, right now the time is {} in {} timezone.
""" # Current prompt for LLM, will adapt for circular chain based on whether questions are answered.


# Configure tool node and LLM
tools = [add_event]

tool_node = ToolNode(tools)

llm = ChatGoogleGenerativeAI(
   model="gemini-1.5-flash", 
   google_api_key=GOOGLE_API_KEY,
   temperature=0.2,
).bind_tools(tools)

# Initialize graph
graph_builder = StateGraph(State)

graph_builder.add_node("event_init", event_init_AI)
graph_builder.add_node("process_response", tool_node)
graph_builder.add_edge(START, "event_init")
graph_builder.add_edge("event_init", "process_response")
graph_builder.add_edge("process_response", END)

graph = graph_builder.compile()

# Invoke graph on sample input
output = graph.invoke({"messages": [("user", "Create me 6 half an hour long meetings Friday afternoon")]})

pprint(output)