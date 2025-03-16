from fastapi import HTTPException
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from gcal_service import GoogleCalendarService

class Session:
   """Class to manage user sessions"""

   _instances: dict = {}

   def user_in_session(cls, user_id: str):
      """Method to check if a user is in session"""

      return user_id in cls._instances
   
   def get_service(cls, user_id: str):
      """Method to retrieve the Google Calendar service object stored for a user"""

      return cls._instances[user_id]["service"] if cls.user_in_session(user_id) else None

   def update(cls, user_id: str, token: str = None):
      """Method to update the session data for a user with a new service object"""

      try: 
         # Build the Google Calendar API service object
         service = GoogleCalendarService(auth_token=token) if token else GoogleCalendarService()

         # Update the session data
         cls._instances[user_id] = {"service": service}

         print("Session data, updated:", cls._instances)

      except HttpError as error:
         raise HTTPException(status_code=500, detail=f"An error occurred: {error}")
      
session = Session()