from datatypes import State, RouterOutput, Agent
from tools import print_state

from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph

class Router(Agent):
    """Router agent; Routes user input to the appropriate agent"""

    def __init__(self, llm):
        # Initialize graph builder
        builder = StateGraph(State)

        # Add nodes
        builder.add_node("router", self.router)

        # Add edges to define flow
        builder.set_entry_point("router") # First invoke lookup to fetch event(s) to edit

        # Set attributes
        self.graph = builder.compile()
        self.llm = llm

    def router(self, state: State):
        """Main node for event_editor"""

        output = self.llm.with_structured_output(RouterOutput).invoke(
        [SystemMessage(content=self.get_instructions())] + state["messages"]
        )

        return {"messages": output.message + "\nHelper agent: " + output.helper_agent, "helper_agent": output.helper_agent}

    get_instructions = lambda self: f"""
        You are the Router agent for a time management AI figure called Indigo. You will be determining whether the user's query is covered by any of the specialized agents, and if so, route the query to the appropriate agent. If not, you will route the query to the general Indigo agent.
    """


def main():

    from langchain_google_genai import ChatGoogleGenerativeAI
    import os
    from dotenv import load_dotenv

    load_dotenv()

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.2
    )

    indigo = Router(llm)

    print_state(indigo.invoke(
        {"messages": [("user", "How can I do that?")]}
    ))

   
if __name__ == "__main__":
    main()