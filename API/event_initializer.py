from datatypes import State
from tools import add_event

import os
import datetime
import pytz
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage

# PERHAPS JUST ONE TOOL NODE FOR ALL AGENTS, BUT DIFFERENT TOOLS ARE BINDING TO THEM AND IMPORTED LIKE THAT. THEN EDGES ARE DONE IN THE BIG ASSEMBLY PROGRAM JUST LIKE NORMAL, CONNECTING ALL AGENTS TO THE TOOL NODE.

load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
   model="gemini-1.5-flash", 
   google_api_key=GOOGLE_API_KEY,
   temperature=0.2,
).bind_tools([
   add_event
])

def events_initializer(state: State):
   """Node for events initializer agent"""

   message = llm.invoke(
      [SystemMessage(content=system_instructions())] + state["messages"]
   )
   return {"messages": message} # return new 'messages' from invokation of llm on current 'messages' stored in state. Then our add_messages function automically appends

def system_instructions():
   """Function to generate system instructions for Gemini"""

   current_time = datetime.datetime.now().isoformat() 
   user_timezone = pytz.timezone(pytz.country_timezones('US')[0])
   return f"""
      You are the Event Initializer agent for a time management AI figure called Indigo. 
      You will take input detailing one or more events to insert, and make the appropriate call to `add_event`. For multiple events, simply make multiple calls to `add_event`.
      The appropriate argument format for `add_event` is detailed in its description and argument details.
      Output a content message detailing how you found this task.
      For context, right now the time is {current_time} in {user_timezone} timezone.
   """ # Current prompt for LLM, will adapt for circular chain based on whether questions are answered.