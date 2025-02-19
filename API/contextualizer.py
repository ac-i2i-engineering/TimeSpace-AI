from datatypes import State, TimeData, Agent
from tools import print_state, list_events

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph

class Contextualizer(Agent):
   """Event initializer agent; Takes user input detailing event(s), adds them to Google Calendar"""

   def __init__(self, llm):
      # Initialize graph builder
      builder = StateGraph(State)
         
      # Add nodes
      builder.add_node("get", self.get_events)
      builder.add_node("summarize", self.summarize)

      # Add edges to define flow
      builder.set_entry_point("get") # Generate function call to add event
      builder.add_edge("get", "summarize") # Executes function call

      # Set attributes
      self.graph = builder.compile()
      self.llm = llm

   def get_events(self, state: State):
      """Node for contextualizer agent to craft function calls to add events"""

      # Invoke initialize node with `add_event` tool and system instructions attached to state messages
      events = list_events.run({"timeMin":TimeData.formatted_time(), "timeMax":TimeData.formatted_time(delta_days=10), "timeZone":str(TimeData.formatted_timezone())})
      
      return {"context": events} # return new 'messages' from invokation of llm on current 'messages' stored in state. Then our add_messages function automically appends
   
   def summarize(self, state: State):
      """Node for event initializer agent to craft function calls to add events"""

      # Invoke summarize node with system instructions attached to context message
      message = self.llm.invoke(
         [SystemMessage(content=self.get_instructions()), HumanMessage(content=state["context"])]
      )
      return {"context": message.content} # return new 'messages' from invokation of llm on current 'messages' stored in state. Then our add_messages function automically appends
   

   # Functions to generate time-aware instructions for the initialize node
   get_instructions = lambda self: f"""
         You are the Contextualizer agent for a time management AI figure called Indigo. 
         You will format the event data you are given into a simple, concise, LLM-understandable report. The purpose of this report is to help other agents make context-aware decisions, so the format should be conducive to LLM understanding. This means you should optimally balance detail with brevity in reporting the user's schedule. Make sure that LLMs will understand it to a point where they won't schedule anything overlapping or overbook the user.
         
         Frame it in terms of busy times for the user.
         Ex: "
            Busy Times, next 10 days (America/New_York timezone):

            * **12:00-13:00, 2025-02-09** (i2i roundtable)
            * **14:00-16:00, every Tuesday and Thursday, starting <office_hours_date>** (Office Hours)
         "

         For context, right now the time is {TimeData.formatted_time()} in {TimeData.formatted_timezone()} timezone.
      """

# TESTING

def main():
   from langchain_google_genai import ChatGoogleGenerativeAI
   import os
   from dotenv import load_dotenv

   load_dotenv()
   
   llm = ChatGoogleGenerativeAI(
      model="gemini-1.5-flash", 
      google_api_key=os.getenv("GEMINI_API_KEY"),
      temperature=0.3
   )

   agent = Contextualizer(llm)
   print_state(agent.invoke(
      {"messages": [("user", "Disneyland tomorrow from 8am to 5pm")], "helper_agent": "", "context": ""}
   ))

   
if __name__ == "__main__":
   main()