from datatypes import State, TimeData, Agent, SelectOutput
from tools import list_events, print_state, parseJSON, get_event, json, print_stream

from langchain_core.messages import SystemMessage, AIMessage
from langgraph.graph import StateGraph

class EventLookup(Agent):
   """Event lookup agent; Takes user input which references certain events, retrieves them from Google Calendar"""
   
   def __init__(self, llm, tool_node):
      # Initialize graph builder
      builder = StateGraph(State)

      # Add nodes
      builder.add_node("query", self.query)
      builder.add_node("tool", tool_node)
      builder.add_node("select", self.select)

      # Add edges to define flow
      builder.set_entry_point("query") # First generates query to retrieve candidate events
      builder.add_edge("query", "tool") # Call tool to list events
      builder.add_edge("tool", "select") # Select correct event(s) from candidate

      # Set attributes
      self.graph = builder.compile()
      self.llm = llm

   def query(self, state: State):
      """Node for event lookup agent to craft a `list_events` query"""

      # Invoke query node with `list_events` tool and system instructions attached to state messages
      output = self.llm.bind_tools([ list_events ], tool_choice="list_events").invoke(
         [SystemMessage(content=self.get_query_instructions())] + state["messages"]
      )

      # Return output to be appended to state
      return {"messages": output}

   def select(self, state: State):
      """Node for event lookup agent to choose relevant events"""

      # Invoke select node with system instructions attached to state messages
      output = self.llm.with_structured_output(SelectOutput).invoke(
         [SystemMessage(content=self.get_select_instructions())] + state["messages"]
      )
      # Use list of IDs to get list of Event objects from Google Calendar API

      events = [get_event(id) for id in output.selection]
      message = AIMessage(content=json.dumps(events))

      # Return output (either list of events or original unparseable output) to be appended to state
      return {"messages": message}
   
   # Functions to generate time-aware instructions for the nodes
   get_query_instructions = lambda self: f"""
         You are the query node for the Event Lookup agent for a time management AI figure called Indigo. You will be given a user prompt that talks about one or more events, and you will generate a query to 'capture' the events referenced in the prompt. Then, the relevant events will be selected from the results of the query by the next node in the agent.
         
         Ex: 'What is my next upcoming event?' -> list_events(maxResults=1, timeMin=<current_time>, singleEvents=True, orderBy='startTime')
         Ex: 'Make my lunch break today 30 minutes' -> list_events(timeMin=<today_begin>, timeMax=<today_end>, singleEvents=True)
         Ex: 'What is my schedule for the rest of the day?' -> list_events(timeMin=<current_time>, timeMax=<today_end>, singleEvents=True)

         - When the user mentions a specific day, set timeMin=<day_begin>, timeMax=<day_end>, and singleEvent=True.
         Ex: 'Delete my haircut tomorrow.' -> list_events(timeMin=<tomorrow_begin>, timeMax=<tomorrow_end>, singleEvents=True)

         Ex: 'Reschedule my gym sessions to 6pm' -> list_events(timeMin=<midnight last night>, timeMax=<midnight two weeks from now>)
         - In the above example, the time frame for the query is ambiguous, so the query is kept broad and singleEvents is left as False so as to appropriately capture potentially recurring events.

         For context, right now the time is {TimeData.formatted_time()} in {TimeData.formatted_timezone()} timezone.
      """
   
   get_select_instructions = lambda self: f"""
         You are an agent in charge of selecting the relevant event(s) from the selection provided by the result of the Tool call. Produce a list of the IDs of the event(s) that the user is 'referencing' in their query. You may assume events are upcoming by default. 
         Select a recurrent event when the user mentions it.
         BE PRECISE ABOUT THIS. If the user mentions events which do not correspond to any of the options, output an empty list []. THIS IS THE DEFAULT BEHAVIOR, i.e. most input possibilities should NOT map to any of the possible options, and should lead you to output an empty list [].

         Ex: User: 'When is my dinner tonight?', Tool: [<Haircut>, <Gym>] -> Output: []
         Ex: User: 'Cancel my haircut tomorrow.', Tool: [<Wake up>, <Gym>] -> Output: []

         Ex: User: 'Cancel my lectures tomorrow', Tool: [<Linear Algebra Lecture>, <Calculus Lecture>] -> Output: [<Linear Algebra Lecture ID>, <Calculus Lecture ID>]
         Ex: User: 'What is my schedule for the rest of the day?', Tool: [] -> Output: []
         Ex: User: 'Push all my meetings this afternoon to tomorrow.', Tool: [<Meeting 1>, <Meeting 2>] -> Output: [<Meeting 1 ID>, <Meeting 2 ID>]
         - The above example shows that the options provided by the tool call *typically* reflect the user's specified time frame, so you don't usually have to worry about that.

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
   tool_node = ToolNode([ list_events ])


   lookup = EventLookup(llm, tool_node)
   print_stream(lookup.stream(
      {"messages": [("user", "Shorten Lunch to 25 minutes")]}, stream_mode="values"
   ))
   
if __name__ == "__main__":
   main()