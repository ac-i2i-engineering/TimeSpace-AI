from typing import Annotated, List, Literal
from typing_extensions import TypedDict

import datetime
import tzlocal

from pydantic import BaseModel, Field, computed_field
from langgraph.graph.message import add_messages
from langchain_core.runnables import Runnable
from langchain_core.messages import ToolMessage

# Define classes for use in tools and graph
class IndigoOutput(BaseModel):
   """Output structure for Indigo agent"""
   
   message: str = Field(..., description="Your message to the user. If helper agents are needed, this should be a status message like 'Adding to your calendar...'. If none are needed, this will be the final message to the user, so include all the information they need from internal messages.")
   helper_agent: Literal["event_initializer", "event_lookup", "event_editor", "none"] = Field(
      ..., 
      description="""Helper agents are how you, as Indigo, perform operations in the user's Google Calendar. If you want to execute an action, specify the appropriate agent here.
      - To put events in the user's calendar, put the 'event_initializer' agent.
      - To find specific events in the user's calendar, put the 'event_lookup' agent. (You will only need this for information not included in the context report you are given)
      - To update/delete/change/edit events in the user's calendar, put the 'event_editor' agent.
      
      Sometimes you will invoke helper agents to perform operations the user doesn't explicitly ask of you. 
      Ex: Indigo: (message='Tell me about some of the things you have scheduled this weekend.', helper_agent='none'), User: 'I have a meeting with John at 2pm on Saturday and a doctor's appointment at 10am on Sunday' -> Indigo: (message='I don't see these in your calendar, would you like me to add them?', helper_agent='none'), User: 'Yes' -> Indigo: (message='Adding events to your calendar', helper_agent='event_initializer')
      
      
      Other times, you will perform operations that the user tells you. Here are some examples of that:
      Ex: 'Make my dinner tonight an hour' -> event_editor
      Ex: 'Schedule me a meeting with John tomorrow at 10am' -> event_initializer
      Ex: 'What is my schedule for the rest of the day?' -> event_lookup
      Ex: 'Push my meeting with John tomorrow to 11am' -> event_editor
      Ex: 'Schedule me a gym session every week day at 11am' -> event_initializer

      After helper agents have executed their operations, you will take the output and use it to inform your message to the user, and if no more helper agents are needed (i.e. the operation you wanted to perform has been performed), put "none" here.

      If you are asking follow-up questions, put "none" here.
      """
   )


class EventBody(BaseModel):
   """Event body for Google Calendar event"""

   summary: str = Field(None, description="Title of the event", example="Meeting with John")
   startTime: str = Field(..., description="DateTime in ISO 8601 format, starting time of the event", example="2024-10-18T10:00:00")
   endTime: str = Field(..., description="DateTime in ISO 8601 format, ending time of the event", example="2024-10-18T11:00:00")
   timeZone: str = Field(..., description="Time zone for the event", example="America/New_York")

   colorId: str = Field(None, description="The color of the event. This is an ID referring to an entry in the event section of the colors definition. Here are standard color IDs, 1: Lavender (faint purple (minty green), 3: Grape (deep pink), 4: Flamingo (muted red), 5: Banana (deep yellow), 6: Tangerine (vibrant orange), 7: Peacock (bright blue), 8: Graphite (grey), 9: Blueberry (deep indigo), 10: Basil (forest green), 11: Tomato (bright red). Optional.")
   description: str = Field(None, description="Description of the event. Can contain HTML. Optional.")
   location: str = Field(None, description="Geographic location of the event as free-form text. Optional.")
   recurrence: List[str] = Field(None, description="List of RRULE, EXRULE, RDATE and EXDATE lines for a recurring event, as specified in RFC5545. Note that DTSTART and DTEND lines are not allowed in this field; event start and end times are specified in the start and end fields. This field is omitted for single events or instances of recurring events.")

   # Model is constructed with parallel properties for better LLM understanding, but nested properties are computed for use in API calls
   @computed_field
   @property
   def start(self) -> dict:
      return {
         "dateTime": self.startTime,
         "timeZone": self.timeZone,
      }
   
   @computed_field
   @property
   def end(self) -> dict:
      return {
         "dateTime": self.endTime,
         "timeZone": self.timeZone,
      }

class ListQuery(BaseModel):
   """Query params for Events: list API call
   Used as args schema for list_events tool"""

   calendarId: str = Field("primary", description="Calendar identifier. To retrieve calendar IDs call the calendarList.list method. If you want to access the primary calendar of the currently logged in user, use the 'primary' keyword.")
   maxResults: int = Field(None, description="Maximum number of events returned on one result page. By default the value is 250 events. Optional.")
   #q: str =	Field(None, description="Free text search terms to find events. Optional.")
   timeMin: str = Field(None, description="Lower bound (exclusive) for an event's end time to filter by. Optional. The default is not to filter by end time. Must be an RFC3339 timestamp with mandatory time zone offset, for example, 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z. Milliseconds may be provided but are ignored. If timeMax is set, timeMin must be smaller than timeMax.")
   timeMax: str = Field(None, description="Upper bound (exclusive) for an event's start time to filter by. Optional. The default is not to filter by start time. Must be an RFC3339 timestamp with mandatory time zone offset, for example, 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z. Milliseconds may be provided but are ignored. If timeMin is set, timeMax must be greater than timeMin.")
   timeZone: str = Field(None, description="Time zone used in the response. Include for our use case. The default is the time zone of the calendar.")
   singleEvents: bool = Field(None, description="Whether to expand recurring events into instances and only return single one-off events and instances of recurring events, but not the underlying recurring events themselves. Set 'True' when specifying maxResults.")
   orderBy: str = Field(None, description="The order of the events returned in the result. By default the events are sorted by start time in ascending order. Optional. Possible values are: 'startTime', 'updated'.")

class SelectOutput(BaseModel):
   """Output structure for Event Lookup agent"""

   selection: List[str] = Field(..., description="List of event IDs selected from the candidate events")


def add(left, right):
   """Add messages together, removing duplicate Tool Messages in accordance with Gemini function call norms"""
   
   first_tool = None

   if isinstance(right, list):
      i = 0
      while i < len(right): # Loop through the right side
         if isinstance(right[i], ToolMessage): # Collapse all tool messages into the first one that appears
            if first_tool is None:
               first_tool = i
            else:
               right[first_tool].content += ", " + right[i].content
               right[first_tool].name += ", " + right[i].name
               right[first_tool].tool_call_id += ", " + right[i].tool_call_id
               right.pop(i)
               i -= 1
         i += 1
   return add_messages(left, right)
   

class State(TypedDict):
   """State class for agent graph"""

   messages: Annotated[list, add]
   helper_agent: Literal["event_initializer", "event_lookup", "event_editor", "indigo"]
   context: str

class TimeData:
   """Standardized functions for exposing time data to LLMs"""

   formatted_time = lambda delta_days=0: (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=delta_days)).astimezone().isoformat()
   formatted_timezone = lambda: tzlocal.get_localzone()

class Agent(Runnable):
   """Base class for agents, extends LangChain Runnable and routes method calls to internal graph object
   Allows instances of agents to be added as nodes in a graph"""

   graph: Runnable

   invoke = lambda self, *args, **kwargs: self.graph.invoke(*args, **kwargs)

   stream = lambda self, *args, **kwargs: self.graph.stream(*args, **kwargs)
