from abc import abstractmethod
import time
from nonebot import require, get_driver, get_plugin_config
from nonebot import on_command
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg
from nonebot.exception import MatcherException
require('bbot_api')
from ... import bbot_api
from ...bbot_api.argparse import ArgParser
from ...bbot_api.message_compat import TextImageMessage

from ..gd_data import AREDL_CACHE,PLAT_CHART_CACHE,PLAT_SHEET_CACHE,UNDERRATED_CACHE,GDDL_BACKUP
from ..data_cache import BaseCache
from ..utils import select_page
from .gdsearch_backend import GDLevelInfoProvider
from ..plat_sheets import LevelEntry
from ..models.gdapi import AREDLLevel
from ..config import Config
from ..utils import searchInName

require('bbot_render')
from ...bbot_render import RenderAPI
from ...bbot_render.models import LevelLargeRenderArgs
require('gd_api')
from ...gd_api.thumbs import getThumbnail_async,getThumbnailUrl

driver=get_driver()
plugin_cfg=get_plugin_config(Config)
render_api=RenderAPI(uri=plugin_cfg.render_server_uri)

gdlocalsearch=on_command("gdlocalsearch")
@gdlocalsearch.handle()
async def _(bot:Bot,event:Event,args: Message = CommandArg()):
    
    supports_image=bbot_api.supportsImage(bot)
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser("gdlocalsearch")
        parser.add_argument('-p',help='Page',type=int)
        parser.add_argument('-f',help="Fuzzy",action='store_true')
        parser.add_argument('--text',help="Plain Text",action='store_true')
        parser.add_argument('--pagesize',help="Page Size",type=int,default=10)
        parser.add_argument('search', nargs='*', type=str, help='search string')
        parsed=parser.parse_args(raw_args)
        
        search=" ".join(parsed.search)
        page=parsed.p or 1
        fuzzy=parsed.f or False
        pagesize = int(parsed.pagesize)
        enable_image=(supports_image and not parsed.text)
        
    except Exception as e:
        await gdlocalsearch.finish(str(e))
        return
    
    
    reply = TextImageMessage.build(bot)
    
    level_ids = SEARCH_MANAGER.search(search,fuzzy)
    levels=[(k,v) for k,v in level_ids.items()]

    count=levels.__len__()
    entries_per_page=pagesize
    results,maxpages,page=select_page(levels,count,entries_per_page,page)
    
    if count==0:
        reply.addLine("Not found")
    elif results.__len__()>1:
        reply.addLine(f"{count} found (Page {page}/{maxpages}):")
    
        for l in results:
            reply.addLine(f"({l[0]}) {l[1][0].name} by {l[1][0].creator} ({','.join([p.provider.cname for p in l[1]])})")
            
    if results.__len__()==1:
        try:
            result=results[0]
            level_id=result[0]
            entries=result[1]
            info_provider=GDLevelInfoProvider(level_id)
            info_provider.fetch()
            info_provider.fetch_GDDL_backup()
            
            reply.addLine(info_provider.repr_level_base())
            
            thumb=await getThumbnail_async(level_id)
            shown_image=False
            
            if enable_image:
                req_id_base=bbot_api.getid(event)
                imargs=LevelLargeRenderArgs()
                info_provider.fillRenderArgs(imargs)
                imargs.level_id=level_id
                imargs.thumbnail=getThumbnailUrl(level_id) if plugin_cfg.render_server_uri.startswith("ws") else thumb or ""
                
                imargs.level_name=entries[0].name
                imargs.creator=entries[0].creator
                
                img=await render_api.render(imargs,request_id=f"{req_id_base}_{time.time()//1}")
                if isinstance(img,bytes):
                    msg2=bbot_api.TextImageMessage.build(bot)
                    msg2.addLine(f"{level_id}")
                    msg2.addImage(img)
                    shown_image=True
                    await msg2.send(gdlocalsearch)
            
            for l in info_provider.getTextDescription(shown_image):
                reply.addLine(l)
        except Exception as e:
            if isinstance(e,MatcherException):
                raise e
            reply.addLine(f"出错: {e}")
        
    await reply.finish(gdlocalsearch)
    
class ProviderMeta:
    def __init__(self,name:str,cname:str|None) -> None:
        self.name=name
        self.cname=cname if (cname is not None) else name
    
class MinimalLevel:
    def __init__(self,id:int,name:str,provider:ProviderMeta,creator:str="") -> None:
        self.id=id
        self.name=name
        self.provider=provider
        self.creator=creator
        
class SearchProvider:
    def __init__(self,name:str,cname:str|None) -> None:
        self.name=name
        self.cname=cname if (cname is not None) else name
    @abstractmethod
    def search(self,search:str,fuzzy:bool) -> list[MinimalLevel]:
        return []
    
class BaseLevelSearchProvider(SearchProvider):
    def __init__(self,data:BaseCache[LevelEntry],name:str,cname:str|None) -> None:
        super().__init__(name,cname)
        self.data=data
    def search(self,search:str,fuzzy:bool):
        levels=self.data.getOrUpdate()
        return [MinimalLevel(l.id,l.name,ProviderMeta(self.name,self.cname),getattr(l,"creator","")) for l in levels if (l.matchesName(search,fuzzy) or str(l.getID())==search)]
    
class AREDLSearchProvider(SearchProvider):
    def __init__(self,data:BaseCache[AREDLLevel],name:str,cname:str|None) -> None:
        super().__init__(name,cname)
        self.data=data
    def search(self,search:str,fuzzy:bool):
        levels=self.data.getOrUpdate()
        return [MinimalLevel(l.level_id,l.name,ProviderMeta(self.name,self.cname),getattr(l,"creator","")) for l in levels if (searchInName(search,l.name,fuzzy) or str(l.getID())==search)]
    
class GDDLCacheProvider(SearchProvider):
    def __init__(self,name:str,cname:str|None) -> None:
        super().__init__(name,cname)
    def search(self,search:str,fuzzy:bool):
        data=GDDL_BACKUP.get()
        if not data:
            return []
        levels=data
        return [MinimalLevel(l.get_id(),l.Name,ProviderMeta(self.name,self.cname),l.Publisher) for l in levels if (searchInName(search,l.Name,fuzzy) or str(l.get_id())==search)]
    
class LocalSearchManager:
    providers:list[SearchProvider]
    def __init__(self) -> None:
        self.providers=[]
    def addProvider(self,provider:SearchProvider):
        self.providers.append(provider)
    def search(self,search:str,fuzzy:bool):
        results_by_id:dict[int,list[MinimalLevel]]={}
        for provider in self.providers:
            results=provider.search(search,fuzzy)
            for r in results:
                if r.id not in results_by_id:
                    results_by_id[r.id]=[]
                results_by_id[r.id].append(r)
        return results_by_id
    
        
SEARCH_MANAGER=LocalSearchManager()
SEARCH_MANAGER.addProvider(GDDLCacheProvider("GDDL","GDDL"))
SEARCH_MANAGER.addProvider(AREDLSearchProvider(AREDL_CACHE,"AREDL","A"))
SEARCH_MANAGER.addProvider(BaseLevelSearchProvider(PLAT_CHART_CACHE,"DiffChart","DC"))
SEARCH_MANAGER.addProvider(BaseLevelSearchProvider(PLAT_SHEET_CACHE,"NLW-Like","NLW"))
SEARCH_MANAGER.addProvider(BaseLevelSearchProvider(UNDERRATED_CACHE,"Underrated","UND"))
    