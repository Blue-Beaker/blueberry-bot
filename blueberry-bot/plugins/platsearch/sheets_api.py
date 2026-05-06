import os.path

from nonebot import on_command,logger,on_startswith,get_plugin_config,on_type,get_adapter

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from nonebot import logger

from cachetools import cached, TTLCache

from .config import Config

plugin_config = get_plugin_config(Config)

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    
class Sheets:
    def init_api(self):
        """Shows basic usage of the Sheets API.
        Prints values from a sample spreadsheet.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("secrets/token.json"):
            creds = Credentials.from_authorized_user_file("secrets/token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if plugin_config.sheets_auth_login and (not creds or not creds.valid):
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "secrets/credentials.json", SCOPES
                )
                creds = flow.run_local_server(host=plugin_config.sheets_auth_host,port=plugin_config.sheets_auth_port,browser=False)
                # Save the credentials for the next run
                with open("secrets/token.json", "w") as token:
                    token.write(creds.to_json())
        self.creds=creds
        
    @cached(cache=TTLCache(maxsize=20,ttl=600))
    def get(self,sheetid:str,range:str):
        try:
            service = build("sheets", "v4", credentials=self.creds)
            # Call the Sheets API
            sheet = service.spreadsheets()
            result = (
                sheet.values()
                .get(spreadsheetId=sheetid, range=range)
                .execute()
            )
            values:list[list[str]] = result.get("values", [])
            return values
        except HttpError as err:
            logger.error(err)