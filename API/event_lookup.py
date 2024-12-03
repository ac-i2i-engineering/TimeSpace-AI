from datatypes import State, EventLookupQuestions
from tools import list_events, tool_node

import os
import datetime
import pytz
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END

load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
   model="gemini-1.5-flash", 
   google_api_key=GOOGLE_API_KEY,
   temperature=0.2,
)

def event_lookup_main(state: State):
   """Main node for event lookup agent, answers questions"""
   print("Main")

   output = llm.with_structured_output(EventLookupQuestions).invoke(
      [SystemMessage(content="You are an agent in charge of lookuping up events. You will determine whether you can answer the required questions from the messages provided to you. If you cannot, fill them in with 'unknown'. If you can, fill them in with the answer, in the exact form that it appears in the messages you are given.")] + state["messages"]
   )
   return {"messages": AIMessage(content="Thinking..."),"questions": output}

def event_lookup_query(state: State):
   """Node for event lookup agent to craft a list events query"""
   print("Query")

   output = llm.bind_tools([ list_events ]).invoke(
      [SystemMessage(content=query_instructions())] + state["messages"]
   )
   return {"messages": output} # return new 'messages' from invokation of llm on current 'messages' stored in state. Then our add_messages function automically appends

def event_lookup_select(state: State):
   """Node for event lookup agent to choose relevant events"""
   print("Select")

   output = llm.invoke(
      [SystemMessage(content="You are an agent in charge of selecting the relevant event(s) from the selection provided by the result of the Tool call. Simply reproduce the JSON array string you are given, only including the objects corresponding to the event(s) that the user is 'referencing' in their query, which is found in the content of the HumanMessage in your State. If you cannot find the specified event(s), respond to the user's query detailing this. BE PRECISE ABOUT THIS. IF THE USER MENTIONS AN EVENT OR EVENTS WHICH DOES/DO NOT CORRESPOND TO ANY OF THE OPTIONS, RESPOND WITH A MESSAGE DETAILING THE ISSUE. THIS IS THE DEFAULT BEHAVIOR, i.e. most input possibilities should NOT map to any of the possible options. For example, if the user mentions an English assignment and they only have Math, TELL THEM THEY HAVE NO ENGLISH.")] + state["messages"]
   )
   return {"messages": output}
   # Put human in loop at this step, perhaps "Can't find any" or "Not sure which one you're talking about."

def query_instructions():
   """Function to generate system instructions for Gemini"""

   current_time = datetime.datetime.now().isoformat() 
   user_timezone = pytz.timezone(pytz.country_timezones('US')[0])
   return f"""
      You are an agent for a Google Calendar AI assistant. You will make a tool call to list_events with a JSON consisting of query parameters to look up a certain event or set of events based on the prompt.
      The supported parameters, in accordance with the Google API documentation for Events: list, are as follows:
      - calendarId    string  Which of the user's calendars to sample. For primary calendar (default behavior) use the "primary" keyword REQUIRED PARAMETER.
      - eventTypes	string	Event types to return. Optional. This parameter can be repeated multiple times to return events of different types. If unset, returns all event types. 
         Acceptable values are: 
         - "birthday": Special all-day events with an annual recurrence.
         - "default": Regular events.
         - "focusTime": Focus time events.
         - "fromGmail": Events from Gmail.
         - "outOfOffice": Out of office events.
         - "workingLocation": Working location events.
      - iCalUID	string	Specifies an event ID in the iCalendar format to be provided in the response. Optional. Use this if you want to search for an event by its iCalendar ID.
      - maxAttendees	integer	The maximum number of attendees to include in the response. If there are more than the specified number of attendees, only the participant is returned. Optional.
      - maxResults	integer	Maximum number of events returned on one result page. The number of events in the resulting page may be less than this value, or none at all, even if there are more events matching the query. Incomplete pages can be detected by a non-empty nextPageToken field in the response. By default the value is 250 events. The page size can never be larger than 2500 events. Optional.
      - orderBy	string	The order of the events returned in the result. Optional. The default is an unspecified, stable order.
         Acceptable values are:
            - "startTime": Order by the start date/time (ascending). This is only available when querying single events (i.e. the parameter singleEvents is True)
            - "updated": Order by last modification time (ascending).
      - pageToken	string	Token specifying which result page to return. Optional.
      - privateExtendedProperty	string	Extended properties constraint specified as propertyName=value. Matches only private properties. This parameter might be repeated multiple times to return events that match all given constraints.
      - sharedExtendedProperty	string	Extended properties constraint specified as propertyName=value. Matches only shared properties. This parameter might be repeated multiple times to return events that match all given constraints.
      - showDeleted	boolean	Whether to include deleted events (with status equals "cancelled") in the result. Cancelled instances of recurring events (but not the underlying recurring event) will still be included if showDeleted and singleEvents are both False. If showDeleted and singleEvents are both True, only single instances of deleted events (but not the underlying recurring events) are returned. Optional. The default is False.
      - showHiddenInvitations	boolean	Whether to include hidden invitations in the result. Optional. The default is False.
      - singleEvents	boolean	Whether to expand recurring events into instances and only return single one-off events and instances of recurring events, but not the underlying recurring events themselves. Optional. The default is False. (USE TRUE FOR OUR USE CASE)
      - timeMax	datetime	Upper bound (exclusive) for an event's start time to filter by. Optional. The default is not to filter by start time. Must be an RFC3339 timestamp with mandatory time zone offset, for example, 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z. Milliseconds may be provided but are ignored. If timeMin is set, timeMax must be greater than timeMin.
      - timeMin	datetime	Lower bound (exclusive) for an event's end time to filter by. Optional. The default is not to filter by end time. Must be an RFC3339 timestamp with mandatory time zone offset, for example, 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z. Milliseconds may be provided but are ignored. If timeMax is set, timeMin must be smaller than timeMax. (USE THE CURRENT TIME FOR OUR USE CASE)
      - timeZone	string	Time zone used in the response. Optional. The default is the time zone of the calendar. (INCLUDE THIS FOR OUR USE CASE)
      - updatedMin	datetime	Lower bound for an event's last modification time (as a RFC3339 timestamp) to filter by. When specified, entries deleted since this time will always be included regardless of showDeleted. Optional. The default is not to filter by last modification time.
      
      Craft your query parameters logically, utilizing query parameters to search for the event or set of events that the prompt is referencing. You can assume that all events the user references are upcoming.
      
      Here are some examples. For an action that mentions "editing the next upcoming event" you might set the timeMin to the current time and maxResults to 1, because all that matters is that one event. For the action that mentions "Changing my meeting on Friday afternoon", you would want to fetch the existing events on Friday afternoon, and so set timeMin to 12:00PM that day and timeMax to 6:00pm that day. 
      DEFAULT BEHAVIOR: Keep the query broad when unsure, so as to provide as much context as possible. DO NOT USE 'q' TO ADD SEARCH TERMS.
      YOUR JSON SHOULD CONTAIN NO ESCAPE CHARACTERS OR MARKDOWN. IT SHOULD SIMPLY BE A PARSABLE STRING OF JSON.
      For context, right now the time is {current_time} in {user_timezone} timezone.
   """ # Current prompt for LLM, will adapt for circular chain based on whether questions are answered.


graph_builder = StateGraph(State)
   
graph_builder.add_node("tool", tool_node)
graph_builder.add_node("query", event_lookup_query)
graph_builder.add_node("select", event_lookup_select)

graph_builder.add_edge(START, "query")
graph_builder.add_edge("query", "tool")
graph_builder.add_edge("tool", "select")
graph_builder.add_edge("select", END)

graph = graph_builder.compile()

def event_lookup(state: State):
   return graph.stream(state, stream_mode="values")


def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()
        print()

def main():
   print_stream(event_lookup({"messages": [("user", "Reschedule my Math study time")], "questions": None}))

   
if __name__ == "__main__":
   main()