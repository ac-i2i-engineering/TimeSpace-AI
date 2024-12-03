from gcal_service import GoogleCalendarService
from datatypes import EventBody

import json

from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

service = GoogleCalendarService()

def parseJSON(json_str: str) -> object:
    """Helper function to convert unpredictable AI JSON output to proper Python object"""
    return json.loads(json_str.replace("\\n", "").replace("\n", "").replace("```json", "").replace("```", "").replace("\\", ""))

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
      return event
    except Exception as e:
        print(f"""{e}\nUnexpected input format: {event_body}""")

@tool
def list_events(query: str):
    """Method to list events based on query, a string of JSON with appropriate query params as detailed in system prompt."""

    params = parseJSON(query)
    print("Parsed params: ", repr(params))
    events_result = service.events().list(
        **params
    ).execute()
    events = events_result.get("items", [])
    return events

tools = [add_event, list_events]

tool_node = ToolNode(tools)