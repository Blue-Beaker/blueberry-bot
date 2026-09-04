
from nonebot import logger,get_plugin_config

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from nonebot import logger

from .config import Config

try:
    plugin_config = get_plugin_config(Config)
except:
    plugin_config = Config()

class Sheet:
    def __init__(self,id:str) -> None:
        self.id=id
    def get_range(self,range:str):
        return get(self.id,range)
    def list_sheet_names(self):
        return list_sheet_names(self.id)
    def get_sheet_size(self, sheet_name:str|None=None, sheet_index:int|None=None):
        return get_sheet_size(self.id, sheet_name=sheet_name, sheet_index=sheet_index)
    def get_row_col_count(self, sheet_name:str|None=None, sheet_index:int|None=None):
        return self.get_sheet_size(sheet_name=sheet_name, sheet_index=sheet_index)
    
class SheetRange(Sheet):
    def __init__(self,id:str,range:str) -> None:
        super().__init__(id)
        self.range=range
    def get(self):
        return get(self.id,self.range)
    def get_sheet_size(self, sheet_name:str|None=None, sheet_index:int|None=None):
        return super().get_sheet_size(sheet_name=sheet_name, sheet_index=sheet_index)
    
def get(sheetid:str,range:str) -> list[list[str]]|None:
    try:
        if not plugin_config.sheets_api_key:
            logger.error("API key not set, sheets won't work!")
            return None
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

def list_sheet_names(sheetid:str) -> list[str]:
    """获取表格中所有工作表(tab)的名称列表, 用于构造 range"""
    try:
        if not plugin_config.sheets_api_key:
            logger.error("API key not set, sheets won't work!")
            return []
        service = build("sheets", "v4", developerKey=plugin_config.sheets_api_key)
        result = (
            service.spreadsheets()
            .get(spreadsheetId=sheetid)
            .execute()
        )
        sheets = result.get("sheets", [])
        names = [s["properties"]["title"] for s in sheets]
        return names
    except HttpError as err:
        logger.error(err)
        return []


def get_sheet_size(sheetid:str, sheet_name:str|None=None, sheet_index:int|None=None) -> tuple[int,int]|None:
    """获取指定工作表的行数和列数。可以按工作表名或索引定位。"""
    try:
        if not plugin_config.sheets_api_key:
            logger.error("API key not set, sheets won't work!")
            return None
        service = build("sheets", "v4", developerKey=plugin_config.sheets_api_key)
        result = (
            service.spreadsheets()
            .get(spreadsheetId=sheetid)
            .execute()
        )
        sheets = result.get("sheets", [])
        target_sheet = None

        if sheet_name is not None:
            for sheet in sheets:
                if sheet.get("properties", {}).get("title") == sheet_name:
                    target_sheet = sheet
                    break
        elif sheet_index is not None:
            if 0 <= sheet_index < len(sheets):
                target_sheet = sheets[sheet_index]
        elif len(sheets) == 1:
            target_sheet = sheets[0]

        if target_sheet is None:
            logger.warning(f"No matching sheet found for {sheetid}: name={sheet_name}, index={sheet_index}")
            return None

        properties = target_sheet.get("properties", {})
        grid_properties = properties.get("gridProperties", {})
        row_count = int(grid_properties.get("rowCount", 0) or 0)
        column_count = int(grid_properties.get("columnCount", 0) or 0)
        return row_count, column_count
    except HttpError as err:
        logger.error(err)
        return None
