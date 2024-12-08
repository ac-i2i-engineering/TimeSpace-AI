from datatypes import State, EventLookupQuestions
from tools import tool_node, update_event, delete_event
from event_lookup import event_lookup

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

def event_editor_main(state: State):
   """Main node for event_editor"""

   output = llm.bind_tools([ update_event, delete_event ]).invoke(
      [SystemMessage(content=editor_instructions())] + state["messages"]
   )
   return {"messages": output}

def editor_instructions():
   """Function to generate system instructions for the editor node"""

   current_time = datetime.datetime.now().isoformat() 
   user_timezone = pytz.timezone(pytz.country_timezones('US')[0])
   return f"""You are an agent responsible for editing given events based on a """
