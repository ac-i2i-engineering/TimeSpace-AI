from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import asyncio
import uuid
from graph import Graph
from fastapi.middleware.cors import CORSMiddleware
from tools import format_namespace

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

state = {
   "messages": [("user", "Onboard")],
   "helper_agent": "",
}

# Define a generator to stream output from the LangGraph graph
async def stream_graph_output(message: str, thread_id: str):   
   input = {
      "messages": [("user", message)],
   }
   stream = graph.stream(input, {"configurable": {"thread_id": thread_id}}, stream_mode="updates", subgraphs=True)
   for namespace, chunk in stream:
      node_name = list(chunk.keys())[0]
      print(
         f"\n---------- Update from {node_name} node in {format_namespace(namespace)} ---------\n"
      )
      messages = chunk[node_name]["messages"] if "messages" in chunk[node_name] else ""
      message = messages if not isinstance(messages, list) else messages[-1]
      output = message.content if not isinstance(message, (tuple, str)) else message
      
      yield f"""data: {output}\n\n"""  # Format as Server-Sent Events (SSE)

# API endpoint to stream output
@app.get("/stream")
async def stream(
   thread_id: str = Query("1", title="Thread ID"), 
   message: str = Query("Hello!", title="User message")
):
   return StreamingResponse(stream_graph_output(message, thread_id), media_type="text/event-stream")