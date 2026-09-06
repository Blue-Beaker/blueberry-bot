from typing import override
from nonebot import require
from .basic_models import BaseSerializableEntry,GenericLevelEntry

require('gd_api')
from ...gd_api import gddl,aredl,pemonlist,platformerlist
    
class GDDLLevel(GenericLevelEntry[gddl.GDDLLevel],gddl.GDDLLevel):
    @override
    def getID(self):
        return self.get_id()
    
class AREDLLevel(GenericLevelEntry[aredl.Level],aredl.Level):
    @override
    def getID(self):
        return self.get_id()
    
class PemonlistLevel(GenericLevelEntry[pemonlist.Level],pemonlist.Level):
    @override
    def getID(self):
        return self.get_id()
    
class TPLLevel(GenericLevelEntry[platformerlist.Level],platformerlist.Level):
    @override
    def getID(self):
        return self.get_id()
    

