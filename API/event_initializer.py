from datatypes import State, TimeData, Agent
from tools import add_event, print_state

from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph

class EventInitializer(Agent):
   """Event initializer agent; Takes user input detailing event(s), adds them to Google Calendar"""

   def __init__(self, llm, tool_node):
      # Initialize graph builder
      builder = StateGraph(State)
         
      # Add nodes
      builder.add_node("tool", tool_node)
      builder.add_node("init", self.initialize)

      # Add edges to define flow
      builder.set_entry_point("init") # Generate function call to add event
      builder.add_edge("init", "tool") # Executes function call

      # Set attributes
      self.graph = builder.compile()
      self.llm = llm

   def initialize(self, state: State):
      """Node for event initializer agent to craft function calls to add events"""

      # Invoke initialize node with `add_event` tool and system instructions attached to state messages
      message = self.llm.bind_tools([ add_event ]).invoke(
         [SystemMessage(content=self.get_instructions())] + state["messages"]
      )
      return {"messages": message} # return new 'messages' from invokation of llm on current 'messages' stored in state. Then our add_messages function automically appends

   # Functions to generate time-aware instructions for the initialize node
   get_instructions = lambda self: f"""
         You are the Event Initializer agent for a time management AI figure called Indigo. 
         You will take input detailing one or more events to insert, and make the appropriate call to `add_event`. For multiple events, simply make multiple calls to `add_event`.

         Make events an hour if duration or end time is not specified, but otherwise do not assume any default values. 
         Ex: 'Lunch at noon' -> add_event(..., startTime=<12pm>, endTime=<1pm>)

         For context, right now the time is {TimeData.formatted_time()} in {TimeData.formatted_timezone()} timezone.
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
   tool_node = ToolNode([ add_event ])

   init = EventInitializer(llm, tool_node)
   print_state(init.invoke(
      {"messages": [("user", "Disneyland tomorrow from 8am to 5pm")]}
   ))

   
if __name__ == "__main__":
   main()