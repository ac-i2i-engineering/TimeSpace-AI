from fastapi import FastAPI, Query, Header
from fastapi.responses import StreamingResponse
from graph import Graph
from fastapi.middleware.cors import CORSMiddleware
from tools import format_namespace, print_stream
from session import session

from langchain_core.messages import AIMessage

# Initialize the FastAPI app
app = FastAPI()

# Configure Cross-Origin Resource Sharing (CORS) Middleware
# This configuration allows requests from any origin, with any method, and any header.
app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],  # Allows all origins
   allow_credentials=True,
   allow_methods=["*"],  # Allows all methods
   allow_headers=["*"],  # Allows all headers
)

graph = Graph()

def process_stream(stream, with_printing=False):
   for namespace, chunk in stream:
      node_name = list(chunk.keys())[0]

      if with_printing: print(
         f"\n---------- Update from {node_name} node in {format_namespace(namespace)} ---------\n"
      )
         
      # Get the messages from the appropriate node in the chunk
      messages = chunk[node_name]["messages"] if "messages" in chunk[node_name] else None

      # Make sure messages are not empty or None
      if messages:
         # Get the relevant message
         message = messages if not isinstance(messages, list) else messages[-1] # If multiple messages, take the last one

         if with_printing: message.pretty_print()

         # If the message is an AIMessage (rather than a HumanMessage or ToolMessage), yield the data to the client
         if isinstance(message, AIMessage):

            # If a status message is supplied, user should see that; otherwise, show the content
            output = message.status if hasattr(message, "status") else message.content
         
            yield f"""data: {output}\n\n"""  # Format as Server-Sent Events (SSE)


def stream_graph_output(message: str, thread_id: str):  
   """Function to stream output from the graph to the client"""

   # Define the initial state input for the graph
   input = {
      "messages": [("user", message)], # User message
      "user_id": thread_id, # User ID, used to grab Google Calendar service object from session in tools
   }

   # Stream the output from the graph
   stream = graph.stream(input, {"configurable": {"thread_id": thread_id}}, stream_mode="updates", subgraphs=True)

   yield from process_stream(stream, with_printing=True)  # Yield the output from the graph

   yield "event: close\ndata: Connection closed by the server.\n\n"  # Signal the end of the stream
   

@app.get("/stream")
async def stream(
   user_id: str = Query("1", title="User ID"), 
   message: str = Query("Hello!", title="User message"),
   authorization: str = Header(None)
):
   """API endpoint to stream graph output to the client"""

   # If authorization header is provided, generation a new service
   if authorization: 
      token = authorization.split(" ")[-1]
      session.update(user_id, token)
   
   # If not authorization header is provided, but the user is not in session, request a new token to instantiate that user's session
   elif not session.user_in_session(user_id):
      return StreamingResponse(
         iter(["event: token_request\ndata: New auth token requested by the server.\n\n"]), 
         media_type="text/event-stream"
      )
      
   return StreamingResponse(
      stream_graph_output(message, user_id), 
      media_type="text/event-stream",
   )