from typing import Annotated
from typing_extensions import TypedDict

from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages

# Define classes for use in tools and graph

class State(TypedDict):
   """State class for agent graph"""
   messages: Annotated[list, add_messages]
   questions: BaseModel

class EventBody(BaseModel):
   """Event body for Google Calendar event"""

   summary: str = Field(description="Title of the event", example="Meeting with John")
   startTime: str = Field(..., description="DateTime in ISO 8601 format, starting time of the event", example="2024-10-18T10:00:00")
   endTime: str = Field(..., description="DateTime in ISO 8601 format, endgin time of the event", example="2024-10-18T11:00:00")
   timeZone: str = Field(..., description="Time zone for the event", example="America/New_York")

class EventLookupQuestions(BaseModel):
   """Questions that must be answered for the logical functionality of event lookup agent"""

   query: str = Field(..., description="What query should be used to list possible events? This should be a JSON with specific query parameters for the list_events tool.")
   selection: str = Field(..., description="Which of the possible events is the user referencing? This should be a JSON with the specific event details.")