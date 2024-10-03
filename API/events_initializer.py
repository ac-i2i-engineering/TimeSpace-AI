# Import necessary packages
""" import semantic_kernel as sk  # Import the semantic_kernel library
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion  # Import OpenAIChatCompletion from the semantic_kernel library
from semantic_kernel import PromptTemplateConfig, PromptTemplate, SemanticFunctionConfig  # Import additional classes from semantic_kernel
from sklearn.feature_extraction.text import TfidfVectorizer  # Import TfidfVectorizer for text vectorization
from sklearn.metrics.pairwise import cosine_similarity  # Import cosine_similarity for computing similarity between texts """
import random  # Import random module for generating random numbers
import time  # Import time module for time-related tasks
import asyncio
import webbrowser

import gcal_scraping_quickstart as gcal;

class EventInitializer:

    def __init__(self):
       self.service = gcal.get_service()
       """  self.weight = weight  # Set the weight (e.g., 0.1, 0.2, 0.8)
       
        
        self.kernel = sk.Kernel()  # Initialize a semantic kernel
        self.kernel.add_chat_service("chat-gpt", OpenAIChatCompletion("gpt-4-1106-preview", api_key, org_id))  # Add OpenAI chat service to the kernel """

    # Async method to generate questions from a lecture content
    async def addEventAIServer(self, action):
        pass
    # Method stub for discuss_with_peer (not implemented)
    
    
    def add_event(self, event_body):
        if not validate_event_body(event_body): return False
        events = self.service.events()
        event = events.insert(calendarId='primary', body=event_body).execute()
        print ('Event created: %s' % event.get('htmlLink'))
        webbrowser.open(event.get('htmlLink'))
    
    def check_scopes(self):
        calendar_list_entry = self.service.calendarList().get(calendarId='primary').execute()
        print(calendar_list_entry)

 
def validate_event_body(event_body):
    return event_body['summary'] and event_body['start'] and event_body['end']

# Testing

def main():
    agent = EventInitializer()
    agent.add_event(event_body={
        'summary': 'New event',
        'start': {
            'dateTime': '2024-10-02T09:00:00-07:00',
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': '2024-10-02T17:00:00-07:00',
            'timeZone': 'America/New_York',
        },
    })

if __name__ == "__main__":
  main()
  