
from nonebot import logger,get_plugin_config

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from nonebot import logger

from .config import Config

plugin_config = get_plugin_config(Config)
    
class Sheet:
    def __init__(self,id:str,range:str) -> None:
        self.id=id
        self.range=range
    def get(self):
        return get(self.id,self.range)
    
def get(sheetid:str,range:str):
    try:
        if not plugin_config.sheets_api_key:
            logger.error("API key not set, sheets won't work!")
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
            
            