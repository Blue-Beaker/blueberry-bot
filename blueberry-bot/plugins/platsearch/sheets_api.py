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
    
class Sheet:
    def __init__(self,id:str,range:str) -> None:
        self.id=id
        self.range=range
    def get(self):
        return get(self.id,self.range)
    
@cached(cache=TTLCache(maxsize=20,ttl=600))
def get(sheetid:str,range:str):
    try:
        if not plugin_config.sheets_api_key:
            logger.error("API key not set, plugin won't work!")
            return []
        service = build("sheets", "v4", developerKey=plugin_config.sheets_api_key)
        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=sheetid, range=range)
            .execute()
        )
        values:list[list[str]] = result.get("values", [])
        
        if not isinstance(values,list):
            return []
        return values
    except HttpError as err:
        logger.error(err)
            
            