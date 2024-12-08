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



@tool
def update_event(event_body: str):
    """Method to update an event based on an updated set of params, a string of JSON as detailed in system prompt."""

    event_body = parseJSON(event_body)
    event = service.events().update(calendarId='primary', eventId=event_body['id'], body=event_body).execute()
    print('Event updated:', event_body)
    return event
    #webbrowser.open(event.get('htmlLink'))  # Open event in Google Calendar UI

@tool
def delete_event(event_id: str):
    """Method to delete an event based on the event's ID string."""
    event = service.events().delete(calendarId='primary', eventId=event_id).execute()
    return event

def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()
        print()

tools = [add_event, list_events]
tool_node = ToolNode(tools)