import webbrowser
import datetime
import gcal_scraping_quickstart as gcal
import os
import google.generativeai as genai
from dotenv import load_dotenv
import asyncio


# Load environment variables from the .env file
load_dotenv()

# Retrieve API keys from environment variables
API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)


class EventInitializer:
    def __init__(self):
        self.service = gcal.get_service()

    # Use Gemini as the event generator
    async def addEventAIServer(self, action):
        print("Action: ", action)

        # Prompt for the Gemini model
        prompt = f"""
            You are a calendar assistant. Based on the following input: '{action}', generate the required JSON for a Google Calendar event.
            The JSON should contain:
            - "summary": a short title for the event,
            - "start": the start time in ISO 8601 format,
            - "end": the end time in ISO 8601 format,
            - "timeZone": the time zone for the event.

            An example format is this:
            {{
                'summary': 'Work on TimeSpace',
                'start': {{
                    'dateTime': datetime.datetime.utcnow().isoformat() + "Z",
                    'timeZone': 'America/New_York',
                }},
                'end': {{
                    'dateTime': (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat() + "Z",
                    'timeZone': 'America/New_York',
                }},
            }}
        """

        # Define the model and generation configuration for Gemini
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
        )

        # Create a chat session with Gemini and send the prompt
        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        f"""
                        You are a calendar assistant. Based on the following input: '{action}', generate the required JSON for a Google Calendar event.
                        The JSON should contain:
                        - "summary": a short title for the event,
                        - "start": the start time in ISO 8601 format,
                        - "end": the end time in ISO 8601 format,
                        - "timeZone": the time zone for the event.

                        An example format is this:
                        {{
                            'summary': 'Meeting with John',
                            'start': {{
                                'dateTime': '2024-10-18T10:00:00',
                                'timeZone': 'America/New_York',
                            }},
                            'end': {{
                                'dateTime': '2024-10-18T11:00:00',
                                'timeZone': 'America/New_York',
                            }},
                        }}
                        """
                    ],
                }
            ]
        )

        # Generate response
        response = chat_session.send_message(prompt + action)
        print("Response: ", response.text)
        return response

    # Insert new event into Google Calendar
    def add_event(self, event_body):
        if not validate_event_body(event_body):
            return False  # Validate event body
        
        event = self.service.events().insert(calendarId='primary', body=event_body).execute()  # Insert event
        
        print('Event created: %s' % event.get('htmlLink'))
        webbrowser.open(event.get('htmlLink'))  # Open event in Google Calendar

    # Testing method to check scopes 
    def check_scopes(self):
        print(self.service.calendarList().get(calendarId='primary').execute())


# Helper method to validate event specifications
def validate_event_body(event_body):
    try:
        return event_body['summary'] and event_body['start'] and event_body['end']
    except KeyError:
        return False


# Testing
async def main():
    agent = EventInitializer()

    # Sample event for the next hour
    agent.add_event(event_body={
        'summary': 'Work on TimeSpace',
        'start': {
            'dateTime': datetime.datetime.utcnow().isoformat() + "Z",
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat() + "Z",
            'timeZone': 'America/New_York',
        },
    })

    # Schedule a meeting using Gemini AI
    event_body = await agent.addEventAIServer("Schedule a meeting tomorrow from 10 AM to 11 AM with John")
    print("Event body: ", event_body)
    agent.add_event(event_body)


if __name__ == "__main__":
    asyncio.run(main())
