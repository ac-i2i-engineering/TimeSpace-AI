# Import necessary packages
import semantic_kernel as sk  # Import the semantic_kernel library
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion  # Import OpenAIChatCompletion from the semantic_kernel library
from semantic_kernel import PromptTemplateConfig, PromptTemplate, SemanticFunctionConfig  # Import additional classes from semantic_kernel
from sklearn.feature_extraction.text import TfidfVectorizer  # Import TfidfVectorizer for text vectorization
from sklearn.metrics.pairwise import cosine_similarity  # Import cosine_similarity for computing similarity between texts
import random  # Import random module for generating random numbers
import time  # Import time module for time-related tasks
import asyncio

class EventInitializer:

    def __init__(self, text):
        self.weight = weight  # Set the weight (e.g., 0.1, 0.2, 0.8)
       
        
        self.kernel = sk.Kernel()  # Initialize a semantic kernel
        self.kernel.add_chat_service("chat-gpt", OpenAIChatCompletion("gpt-4-1106-preview", api_key, org_id))  # Add OpenAI chat service to the kernel

    # Async method to generate questions from a lecture content
    async def addEventAIServer(self, action):
        new_action = ""  # Initialize a variable to store processed lecture content
        arr = action.split(".") 
        # Process lecture content
        for line in arr:
            r = random.random()  # Generate a random number
            if r < self.retention_rate:
                new_action += line + ".\n"  # Add lines to new content based on retention rate

        action = new_action  # Update lecture content

        # Create and execute a semantic function to generate questions
        return self.kernel.create_semantic_function(f"""You have to perfom a specific action in the calendar defined by:{action}: Pretend that you are an agent who is able to perform actions on the calendar, you have the following abilities {self.educational_background}, and you can ask questions if the instructions are unclear with rate {self.question_rate}. Pretend to be a calendar agent described above who has to perform actions on the personalized google calendar, state one succinct clarifying question you have about the action described and explain to the Central agent which part of the lecture your confusion originated from, and do not state anything other than the question. If you do not want to ask a question respond by saying -1""", max_tokens=200, temperature=0.5)()

    # Method stub for discuss_with_peer (not implemented)
    async def discuss_with_peer(self, peer, action):
        pass  # Placeholder for future implementation