import json
import threading
import time
from typing import cast, override
from nonebot import logger, require,get_driver
from pathlib import Path

require("gd_api")
from ...gd_api.gddl.models import GDDLDifficulty
from ..data_cache import BaseSerializableEntry,CacheWithIDMap

require("bbot_api")
from ...bbot_api.sheets_api import SheetRange

from ..models.gdapi import GDDLLevel

from ..utils import safeConversion

GDDL_BACKUP_SHEET=SheetRange("1qKlWKpDkOpU1ZF6V6xGfutDY2NvcA8MNPnsv6GBkKPQ","GDDL!A2:G")

# debug_path = Path("test_output")

# driver = get_driver()
# @driver.on_startup
# async def _():
#     pass
#     entries=gddl_load_files()
#     logger.info(f"Loaded GDDL Backup Entries: {entries.__len__()}")
#     # threading.Thread(target=gddl_update_thread,name="GDDL Update").start()
    
# def gddl_update_thread():
#     size=GDDL_BACKUP_SHEET.get_sheet_size("GDDL")
#     logger.info(f"Sheet size = {size}")
    
#     if not size:
#         return
    
#     start_time=time.time()
#     sheet = GDDL_BACKUP_SHEET.get()
        
#     with open(debug_path/"gddl.json","w") as f:
#         json.dump(sheet,f)
        
#     end_time=time.time()
#     logger.info(f"GDDL Backup Sheet Download Complete, took {(end_time-start_time):.2f}s")
    
# def gddl_load_files():
#     with open(debug_path/"gddl.json","r") as f:
#         lines=cast(list[list[str]],json.load(f))
#     entries=load_gddl_entries(lines)
#     return entries

def update_gddl_entries():
    size=GDDL_BACKUP_SHEET.get_sheet_size("GDDL")
    logger.info(f"Prepare to update GDDL Backup Sheet, size = {size}")
    
    start_time=time.time()
    sheet = GDDL_BACKUP_SHEET.get()
    if not sheet:
        logger.error(f"Failed to update GDDL Backup Sheet.")
        return None
    
    entries=load_gddl_entries(sheet)
    end_time=time.time()
    logger.info(f"GDDL Backup Sheet updated, took {(end_time-start_time):.2f}s")
    
    return entries
    
def load_gddl_entries(lines:list[list[str]]):
    entries:list[GDDLSheetEntry]=[]
    for l in lines:
        entry=GDDLSheetEntry().load_line(l)
        if entry.getID()==-1:
            continue
        
        entries.append(entry)
    return entries

class GDDLSheetEntry(GDDLLevel):
    @override
    def getID(self) -> int:
        return self.get_id()
    def load_line(self,line:list[str]):
        line=line.copy()
        while line.__len__()<7:
            line.append('')
            
        self.ID=safeConversion(line[0],int,-1)
        self.Name=safeConversion(line[1],str,'')
        self.Publisher=safeConversion(line[2],str,'')
        self.SongName=safeConversion(line[3],str,'')
        self.Difficulty=safeConversion(line[4],GDDLDifficulty,GDDLDifficulty.HARD)
        self.Rating=safeConversion(line[5],float,-1)
        self.Enjoyment=safeConversion(line[6],float,-1)
        return self