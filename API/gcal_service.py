import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

# Define the scope for Google Calendar API
SCOPES = ["https://www.googleapis.com/auth/calendar"]

class GoogleCalendarService:
    """Wrapper class for building Google Calendar service"""

    def __init__(self, auth_token=None):
        """Initializes the Google Calendar service object"""

        self.creds = Credentials(auth_token) if auth_token else None # Initialize credentials from auth token if provided

        self._service: Resource = None # Initialize service object
        self.build_service() # Build service object

    def __getattr__(self, name):
        """Reroutes all other calls to Google service"""
        if self._service is None:
            raise RuntimeError("Service not initialized. Make sure authentication succeeded.")
        return getattr(self._service, name) # Reroute calls to service object
    
    def build_service(self):
        """Initializes the Google Calendar API service."""

        # If service object initialized without credentials, try to authenticate with local credentials
        if not self.creds: self.local_auth()

        # Instantiate service with credentials
        try:
            self._service = build("calendar", "v3", credentials=self.creds)
        except HttpError as error:
            print(f"An error occurred: {error}")

    def local_auth(self):
        """Authenticates the user using local credentials"""

        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        # If credentials are invalid or not present, prompt user for login
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save credentials in "token.json" for future use
            with open("token.json", "w") as token:
                token.write(self.creds.to_json())

# Testing
if __name__ == "__main__":

    # Instatiate service and query for all events
    calendar_service = GoogleCalendarService()
    events = calendar_service.events().list(calendarId='primary').execute() 

    print(events.get('items', [])) # print events
