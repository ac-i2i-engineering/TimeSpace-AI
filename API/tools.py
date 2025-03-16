from gcal_service import GoogleCalendarService
from datatypes import EventBody, ListQuery, State, Annotated, Optional, List, Union

from session import session

import json

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

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

def args_to_dict(args, excluded_keys=["func", "state"]):
    """Helper function to convert function arguments to a dictionary"""

    return {k: v for k, v in args if k not in excluded_keys and v is not None}

@tool
def add_event(
        # Required arguments
        startTime: str,
        endTime: str,
        timeZone: str,

        state: Annotated[State, InjectedState], # Injected state object

        # Optional arguments
        summary: str = None,
        colorId: str = None,
        description: str = None,
        location: str = None,
        recurrence: List[str] = None,
    ):
    """Method to insert event into Google Calendar using API.
    
    Args:
        startTime: DateTime in ISO format, starting time of the event (e.g., "2024-10-18T10:00:00")
        endTime: DateTime in ISO format, ending time of the event (e.g., "2024-10-18T11:00:00") 
        timeZone: Time zone for the event (e.g., "America/New_York")
        summary: Title of the event (e.g., "Meeting with John")
        colorId: The color of the event. This is an ID referring to an entry in the event section of the colors definition. 
            Here are standard color IDs, 1: Lavender (faint purple (minty green), 3: Grape (deep pink), 4: Flamingo (muted red), 5: Banana (deep yellow), 6: Tangerine (vibrant orange), 7: Peacock (bright blue), 8: Graphite (grey), 9: Blueberry (deep indigo), 10: Basil (forest green), 11: Tomato (bright red).
        description: Description of the event. Can contain HTML.
        location: Geographic location of the event as free-form text
        recurrence: List of RRULE, EXRULE, RDATE and EXDATE lines for recurring events
    """
    
    # Construct event body dictionary by passing arguments to EventBody model and dumping, excluding start and end times
    event_body = EventBody(
        **args_to_dict(locals().items())
    ).model_dump(exclude={"startTime", "endTime"})

    # Get user ID from state and get service object from session
    user_id = state["user_id"]
    service = session.get_service(user_id)

    event = service.events().insert(calendarId='primary', body=event_body).execute()  # Insert event
    #webbrowser.open(event.get('htmlLink')) # Open event in Google Calendar UI
    return ("Event added", event)

@tool(args_schema=ListQuery)
def list_events(**kwargs):
    """Method to list events based on query, a string of JSON with appropriate query params as detailed in system prompt."""
    
    params = ListQuery(**kwargs).model_dump()
    events_result = service.events().list(
        **params
    ).execute()
    events = events_result.get("items", [])
    return json.dumps(prune_events(events), indent=3)

@tool
def update_event(
        state: Annotated[State, InjectedState],
        event_body: str = ""
    ):
    """Method to update an event based on an updated set of params, a string of JSON as detailed in system prompt."""

    if not event_body:
        return "Found nothing to update."
    
    event_body = parseJSON(event_body)
    event = service.events().update(calendarId='primary', eventId=event_body['id'], body=event_body).execute() # Update event
    return ("Event updated", event)
    #webbrowser.open(event.get('htmlLink'))  # Open event in Google Calendar UI

@tool
def delete_event(event_id: str = ""):
    """Method to delete an event based on the event's ID string."""

    if not event_id:
        return "Found nothing to update."
    
    event = service.events().delete(calendarId='primary', eventId=event_id).execute()
    return ("Event deleted", event)
    
@tool
def complain(issue: str) -> str:
    """Method to call when unable to complete task, either insufficient input or error. Detail the issue here."""
    return issue


def get_event(event_id: str):
    """Method to delete an event based on the event's ID"""

    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    return event



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

tools = [add_event, list_events, update_event, delete_event, complain]