from gcal_service import GoogleCalendarService
from datatypes import EventBody, ListQuery, State
from langgraph.types import Command, interrupt
import json

from langchain_core.tools import tool

service = GoogleCalendarService()

def parseJSON(json_str: str) -> object:
    """Helper function to convert unpredictable AI JSON output to proper Python object"""

    stripped = json_str.replace("\\n", "").replace("\n", "").replace("```json", "").replace("```", "").replace("\xa0", "")
    
    return json.loads(stripped)

def prune_events(obj: object):
    """Filters out non-identifying properties for more concise representation"""

    excluded = [
        'kind', 
        'etag', 
        'htmlLink', 
        'sequence', 
        'iCalUID',
        'reminders', # not currently supported
        'creator', # not currently supported
        'organizer', # not currently supported
        'created', # potentially unnecessary
        'updated' # potentially unnecessary
    ]

    if isinstance(obj, dict):
        return {k: v for k, v in obj.items() if k not in excluded}
    elif isinstance(obj, list):
        return [prune_events(event) for event in obj]
    return obj

@tool(args_schema=EventBody)
def add_event(**kwargs):
    """Method to insert event into Google Calendar using API."""

    try:
        event_body = EventBody(**kwargs).model_dump(exclude={"startTime", "endTime"})

        event = service.events().insert(calendarId='primary', body=event_body).execute()  # Insert event
        #webbrowser.open(event.get('htmlLink')) # Open event in Google Calendar UI
        return event
    
    except Exception as e:
        return e

@tool(args_schema=ListQuery)
def list_events(**kwargs):
    """Method to list events based on query, a string of JSON with appropriate query params as detailed in system prompt."""
    try:
        params = ListQuery(**kwargs).model_dump()
        events_result = service.events().list(
            **params
        ).execute()
        events = events_result.get("items", [])
        return json.dumps(prune_events(events), indent=3)
    except Exception as e:
        return e

@tool#(args_schema=EventBody)
def update_event(event_body: str = ""):
    """Method to update an event based on an updated set of params, a string of JSON as detailed in system prompt."""

    if not event_body:
        return "Found nothing to update."

    try: 
        event_body = parseJSON(event_body)
        event = service.events().update(calendarId='primary', eventId=event_body['id'], body=event_body).execute() # Update event
        return event   
    except Exception as e:
        return e
    #webbrowser.open(event.get('htmlLink'))  # Open event in Google Calendar UI

@tool
def delete_event(event_id: str = ""):
    """Method to delete an event based on the event's ID string."""

    if not event_id:
        return "Found nothing to update."
    
    try:
        event = service.events().delete(calendarId='primary', eventId=event_id).execute()
        return event
    except Exception as e:
        return e


def get_event(event_id: str):
    """Method to delete an event based on the event's ID"""
    try: 
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        return event
    except Exception as e:
        return e



def format_namespace(namespace):
    return (
        namespace[-1].split(":")[0] + " subgraph"
        if len(namespace) > 0
        else "parent graph"
    )

def print_stream(stream):
    for namespace, chunk in stream:
        node_name = list(chunk.keys())[0]
        print(
            f"\n---------- Update from {node_name} node in {format_namespace(namespace)} ---------\n"
        )
        messages = chunk[node_name]["messages"] if "messages" in chunk[node_name] else ""
        message = messages if not isinstance(messages, list) else messages[-1]
        message.pretty_print() if not isinstance(message, (tuple, str)) else message
        
        print()
        

def print_state(state: State):
    for message in state["messages"]: 
        print("\n", getattr(message, "node", "")), message.pretty_print() if not isinstance(message, tuple) else print(message)
    print("Helper Agent:", state["helper_agent"])
    print("Context:", state["context"])

tools = [add_event, list_events, update_event, delete_event]