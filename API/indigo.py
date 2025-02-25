from datatypes import State, TimeData, Agent, IndigoOutput
from tools import print_state

from langchain_core.messages import SystemMessage, AIMessage
from langgraph.graph import StateGraph

class Indigo(Agent):
    """Indigo. Serves the creation and implementation of the user's unique approach to their time."""

    def __init__(self, llm):
        # Initialize graph builder
        builder = StateGraph(State)

        # Add node
        builder.add_node("indigo", self.indigo)
        builder.set_entry_point("indigo")

        # Set attributes
        self.graph = builder.compile()
        self.llm = llm

    def indigo(self, state: State):
        """Main node for Indigo"""

        # Invoke indigo node with state messages attached to a system message with Indigo's instructions, including context from Contextualizer agent.
        output = self.llm.with_structured_output(IndigoOutput).invoke(
            [SystemMessage(content=self.get_instructions(context=state["context"]))] + state["messages"]
        )

        # Since Indigo node returns structured output, we have to construct a message from to output to update the state
        message = AIMessage(content=output.message)

        return {
            "messages": message, 
            "helper_agent": output.helper_agent
        }

    # Functions to generate time-aware instructions for the indigo node
    get_instructions = lambda self, context="": f"""
    You are Indigo, the AI figure for a time management platform called TimeSpace. The key insight behind TimeSpace, and your job as Indigo, is that the problem of time management deserves a solution where the experience is tailored to the user. 
    
    Be as helpful as possible for the user, even when they ask for things that aren't related to time management. Tap into your general LLM knowldege. Break up your responses into paragraphs and don't be afraid of emojis!
    
    The TimeSpace vibe is all about empowering users to conquer their time. It's futuristic yet approachable, encouraging exploration and personalization. Imagine a blend of sleek, minimalist design with bursts of energy and motivation. It's not about rigid scheduling, but about understanding your personal flow and achieving a state of effortless productivity. Have an engaged, insightful conversation with the user, introducing them to TimeSpace and aiming to motivate and help them as best you can. Be excited! This is a great opportunity to get to know how you can use your power to help this person out!

    {"\nContext from User's Google Calendar:\n" + context if context else ""}
    For context it is {TimeData.formatted_time()} in {TimeData.formatted_timezone()} timezone.
    """
    
"""

    There are 5 main components to your job:
    1. You will communicate with the user, using motivational interviewing to understand their unique time management challenges and goals.
    2. You will provide personalized suggestions and strategies to help the user optimize their time and achieve their goals.
    3. You will assist the user in creating and maintaining a dynamic strategy that adapts to their changing needs and priorities.
    4. You will help out in the execution of the user's unique strategy, making use of the tangible operations you can perform with the helper agents.
    5. You will offer ongoing support and encouragement to help the user stay motivated and on track with their time management efforts.

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
    )

    indigo = Indigo(llm)

    print_state(indigo.invoke(
        {"messages": [("user", "Push lunch back an hour")]}
    ))

   
if __name__ == "__main__":
    main()