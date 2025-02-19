from datatypes import State, TimeData, Agent
from tools import update_event, delete_event, list_events, print_state, print_stream
from event_lookup import EventLookup

from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph

class EventEditor(Agent):
   """Event editor agent; Takes user input detailing event(s) and edits, and updates them in Google Calendar"""

   def __init__(self, llm, tool_node, event_lookup: EventLookup):
      # Initialize graph builder
      builder = StateGraph(State)

      # Add nodes
      builder.add_node("lookup", event_lookup)
      builder.add_node("edit", self.edit)
      builder.add_node("tool", tool_node)

      # Add edges to define flow
      builder.set_entry_point("lookup") # First invoke lookup to fetch event(s) to edit
      builder.add_edge("lookup", "edit") # Generate calls to update and delete
      builder.add_edge("edit", "tool") # Execute calls

      # Set attributes
      self.graph = builder.compile()
      self.llm = llm

   def edit(self, state: State):
      """Main node for event_editor"""

      # Invoke edit node with `update_event` and `delete_event` tools and system instructions attached to state messages
      output = self.llm.bind_tools([ update_event, delete_event ], tool_choice="any").invoke(
         [SystemMessage(content=self.get_instructions())] + state["messages"]
      )

      return {"messages": output}
   
   # Functions to generate time-aware instructions for the edit node
   get_instructions = lambda self: f"""
         You are an agent responsible for editing given events based on a user prompt. You will be given an array of events from the lookup agent in the most recent message, which tries to identify the events specified in the user's prompt.
         For EACH event make the proper call to `update_event`/`delete_event`. `delete_event` is simple, just pass in the event id, but for `update_event` pass the FULL JSON, but with the proper updates to the properties. Be sure to preserve the duration of the events unless specified. 
         
         If the array of events is empty, pass no args to `update_event`/`delete_event`.
         Ex: User: 'Edit my gym session tomorrow to be recurring on weekdays', Lookup: [] -> update_event()
         Ex: User: 'Delete my haircut this afternoon', Lookup: [] -> delete_event()

         For context it is {TimeData.formatted_time()} in {TimeData.formatted_timezone()} timezone.
      """

# TESTING

def main():

   from langchain_google_genai import ChatGoogleGenerativeAI
   from langgraph.prebuilt import ToolNode
   import os
   from dotenv import load_dotenv

   load_dotenv()
   
   llm = ChatGoogleGenerativeAI(
      model="gemini-1.5-flash", 
      google_api_key=os.getenv("GEMINI_API_KEY"),
      temperature=0.3
   )

   tool_node = ToolNode([ update_event, delete_event, list_events ])

   lookup = EventLookup(llm, tool_node)

   editor = EventEditor(llm, tool_node, lookup)

   print_state(editor.invoke(
      {"messages": [("user", "Edit my gym session tomorrow to be recurring on weekdays")]}
   ))

   
if __name__ == "__main__":
   main()