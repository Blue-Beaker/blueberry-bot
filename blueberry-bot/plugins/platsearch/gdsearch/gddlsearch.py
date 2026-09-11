import asyncio
import math
import time
import traceback
from typing import Callable, Generic, Type, TypeVar
from nonebot import on_command,logger,get_plugin_config
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg
from nonebot.exception import MatcherException
from nonebot import get_driver,require

from ..config import Config
from ..utils import repr_level
from ..gd_data import PLAT_CHART_CACHE,AREDL_CACHE,TPL_CACHE

require('bbot_api')
from .. import bbot_api
from ...bbot_api.argparse import ArgParser
require('gd_api')
from ...gd_api.gd import getLevelSearch2_async,LevelSearchType,downloadLevel2_async,getLevelsFromUser_async,getSong_async
from ...gd_api import gd
from ...gd_api.gd import Level
from ...gd_api.thumbs import getThumbnail_async,getThumbnailUrl
from ...gd_api.gddl.search import getGDDLLevel,searchGDDLLevel
from ...gd_api.gddl.search_args import GDDLSearchArgs,Length,Difficulty,TwoPlayer,Sort,SortDir
from ...gd_api.gddl.models import GDDLTags

require("bbot_perms")
from ...bbot_perms import get_perms

from ..utils import repr_level,ensure_gd_level,SearchException

from .gdsearch_backend import GDLevelInfoProvider
from ..formatters import formatGDDLLevel

try:
    require("orb_api")
    from ... import orb_api
except:
    orb_api=None
    
driver=get_driver()
plugin_cfg=get_plugin_config(Config)

require('bbot_render')
from ...bbot_render import RenderAPI
from ...bbot_render.models import LevelLargeRenderArgs
render_api=RenderAPI(uri=plugin_cfg.render_server_uri)

_DIFFICULTY_MAPPINGS:dict[str,Difficulty]={
}
_LENGTH_MAPPINGS:dict[str,Length]={l.name.lower():l for l in Length}

def update_diff_aliases():
    _DIFFICULTY_MAPPINGS.update({k.name.lower():k for k in Difficulty})
    
    ALIASES={
        Difficulty.OFFICIAL:["off","rob"],
        Difficulty.EASY:["ezd","ezp"],
        Difficulty.MEDIUM:["med","mep"],
        Difficulty.HARD:["hdd","hdp"],
        Difficulty.INSANE:["insd","insp"],
        Difficulty.EXTREME:["exd","exp"]
    }
    for diff,keys in ALIASES.items():
        for key in keys:
            _DIFFICULTY_MAPPINGS[key]=diff

class SearchTypeArg:
    search_type:LevelSearchType
    help_str:str
    def __init__(self,search_type:LevelSearchType,help_str:str) -> None:
        self.search_type=search_type
        self.help_str=help_str

_T = TypeVar('_T')
_T2 = TypeVar('_T2')
class BaseArg(Generic[_T]):
    help_str:str
    input_type:Type[_T]
    def __init__(self,help_str:str,input_type:Type[_T]) -> None:
        self.help_str=help_str
        self.input_type=input_type
    def apply(self,searchArgs:GDDLSearchArgs,value:_T):
        pass

class TemplateArg(BaseArg[_T],Generic[_T,_T2]):
    attr_name:str
    help_str:str
    input_type:Type[_T]
    target_converter:Callable[[_T],_T2|None]|None
    def __init__(self,attr_name:str,help_str:str,input_type:Type[_T],target_converter:Callable[[_T],_T2|None]|None=None) -> None:
        super().__init__(help_str,input_type)
        self.attr_name=attr_name
        self.target_converter=target_converter
    def apply(self,searchArgs:GDDLSearchArgs,value:_T):
        setattr(searchArgs,self.attr_name,self.target_converter(value) if self.target_converter else value)
        
class RangeArg(BaseArg[str],Generic[_T2]):
    attr_name_1:str
    attr_name_2:str
    target_converter:Callable[[str],_T2]|None
    def __init__(self, attr_name_1:str, attr_name_2:str, help_str: str, target_converter: Callable[[str], _T2] | None = None) -> None:
        super().__init__(help_str, str)
        self.attr_name_1=attr_name_1
        self.attr_name_2=attr_name_2
        self.target_converter=target_converter
    def apply(self,searchArgs:GDDLSearchArgs,value:str):
        conv=self.target_converter or str
        if '-' in value:
            spl=value.split('-')
            
            low=conv(spl[0].strip())
            high=conv(spl[1].strip())
        else:
            low=conv(value.strip())
            high=low
        
        setattr(searchArgs,self.attr_name_1,low)
        setattr(searchArgs,self.attr_name_2,high)
        
def get_tag_id_from_name(value:str):
    try:
        return int(value)
    except:
        key=value.upper().strip().replace(" ","_")
        try:
            tag = GDDLTags.__getitem__(key)
            return int(tag.value)
        except KeyError:
            raise KeyError(f"Tag不存在: {key}")

_FLAGS:dict[str,BaseArg]={
    "--2-player":TemplateArg("twoPlayer","2-Player",str,TwoPlayer),
    "--sort":TemplateArg("sort","Sort By",str,Sort),
    "--sort-dir":TemplateArg("sortDirection","Sort Direction",str,SortDir),
    "--song":TemplateArg("song","Song Name",str,str),
    "-u":TemplateArg("creator","From Creator",str,str),
    "--top-skill":TemplateArg("topTagId","Tag ID",str,get_tag_id_from_name),
    "--skill":TemplateArg("hasSkillset","Has Skillset",str,get_tag_id_from_name),
    
    "-t":RangeArg("minRating","maxRating","Tier Range (low-high)",float),
    "-e":RangeArg("minEnjoyment","maxEnjoyment","Enjoyment Range",float),
    "--deviation":RangeArg("minDeviation","maxDeviation","Deviation Range",float),
    "--enj-count":RangeArg("minEnjoymentCount","maxEnjoymentCount","Enjoyment Count Range",int),
    "--sub-count":RangeArg("minSubmissionCount","maxSubmissionCount","Submission Count Range",int),
    "--seconds":RangeArg("minSeconds","maxSeconds","Seconds Range",float),
    "--objects":RangeArg("minObjects","maxObjects","Objects Range",int),
    "--id-range":RangeArg("minId","maxId","ID Range",int),
}

update_diff_aliases()

gddlsearch = on_command("gddlsearch")
@gddlsearch.handle()
async def _(bot:Bot, event:Event, args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    try:
        searchArgs=GDDLSearchArgs()
        
        parser=ArgParser("gddlsearch")
        
        group_length=parser.add_mutually_exclusive_group()
        group_length.add_argument('--plat',help='Platformer only',action='store_true')
        
        group_length.add_argument('-l',help='length',type=str,default="")
        
        parser.add_argument('-d',help='Difficulty',type=str,default="")
        parser.add_argument('-v',help='Show Other Info (Time, Upload/Update date, ...)',action='store_true')
        parser.add_argument('--text',help='Plain Text',action='store_true')
        parser.add_argument('-i',help='Show Thumbnail',action='store_true')
        
        parser.add_argument('-p',help='Page',type=int,default=0)
        
        filters=parser.add_argument_group("Search Filters")
        for key,entry in _FLAGS.items():
            if entry.input_type==bool:
                filters.add_argument(key,help=entry.help_str,action='store_true')
            else:
                filters.add_argument(key,help=entry.help_str,type=entry.input_type)
        
        parser.add_argument('search', nargs='*', type=str, help='search string')
        parsed=parser.parse_args(raw_args)
        
        search=" ".join(parsed.search)
        searchArgs.name=search
        
        plat_only=bool(parsed.plat)
        if plat_only:
            searchArgs.length=Length.PLAT
                
        for key,entry in _FLAGS.items():
            name=key.removeprefix("-").removeprefix("-").replace("-","_")
            value=getattr(parsed,name,None)
            if value is not None:
                entry.apply(searchArgs,value)
        
        lengths:list[Length]=[]
        
        for l in str(parsed.l).lower().split(","):
            if l in _LENGTH_MAPPINGS:
                lengths.append(_LENGTH_MAPPINGS[l])
        
        diff = str(parsed.d)
        if diff in _DIFFICULTY_MAPPINGS:
            searchArgs.difficulty=_DIFFICULTY_MAPPINGS[diff]
            if diff.endswith("p") or diff=="pemon":
                plat_only=True
        
        page=int(parsed.p)
        
        searchArgs.page=page
        
        verbose=bool(parsed.v)
        force_text=bool(parsed.text)
        show_thumbnail=bool(parsed.i)
        
        logger.info(f"gddlsearch: {parsed.__dict__}")
        logger.info(searchArgs.getData())
        
    except Exception as e:
        await gddlsearch.finish(str(e))
        return
    
    lines=bbot_api.TextImageMessage.build(bot)
    
    await bbot_api.trigger_typing(bot,event)
    
    results,errors=await searchGDDLLevel(searchArgs)
    
    try:
        if (not results) or errors:
            raise SearchException(f"查找出错: {errors}")
        if results.levels.__len__()==0:
            raise SearchException("没有查找到任何关卡.")
        elif results.levels.__len__()>1:
            lines=[]
            lines.append("找到多个关卡,请用id选择:")
            lines.append(f"第 {results.page}/{math.ceil(results.total/results.limit)} 页 ({results.page*results.limit+1}-{(results.page+1)*results.limit}/{results.total})")
            for l in results.levels:
                lines.append(formatGDDLLevel(l.to_gddl_level(),True,False))
            raise SearchException("\n".join(lines))
    except SearchException as e:
        await gddlsearch.finish(await bbot_api.auto_pack_message(bot,e.msg,6))
        return
    
    gddl_search_level=results.levels[0]
    
    level_id=gddl_search_level.get_id()
    
    supports_image=bbot_api.supportsImage(bot)
    show_thumbnail = (show_thumbnail and supports_image)
    enable_image=(not force_text) and supports_image
    
    level2=None
    thumb=None
    
    try:
        # Async gatherers. return None instantly for unneeded ones
        async def gather_level2():
            level2=None
            orb_account=None
            if not verbose:
                return None
            if orb_api:
                orb_account=orb_api.OrbAccount.fromEvent(event)
                if not orb_account:
                    return
                
                if orb_account.get()<25:
                    lines.addLine("额外信息需要持有 25 Orbs. 消耗可低于此值.")
                else:
                    level2,result=await downloadLevel2_async(level_id)
                    if level2 and level2.level_string:
                        cost=min(25,level2.level_string.__len__()//100000)
                        orb_account.add(-cost)
                        lines.addLine(f"已消耗 {cost} Orbs.")
                    elif result:
                        lines.addLine(f"获取完整信息失败: {result.error}")
            else:
                level2,result=await downloadLevel2_async(level_id)
                if (not level2) and result:
                    lines.addLine(f"获取完整信息失败: {result.error}")
            return level2
        
        async def gather_thumbnail():
            if show_thumbnail or enable_image:
                return await getThumbnail_async(level_id)
            return None
        
        async def gather_gddl():
            gddl_level,e1,e2,e3=await getGDDLLevel(level_id)
            if e1:
                lines.addLine(f"获取关卡出错: {e1}")
            if e2:
                lines.addLine(f"获取Tags出错: {e2}")
            if e3:
                lines.addLine(f"获取Eligible出错: {e3}")
            return gddl_level
        
        level2, thumb, gddl_level = await asyncio.gather(gather_level2(),gather_thumbnail(),gather_gddl())
        
        if not gddl_level:
            gddl_level=gddl_search_level.to_gddl_level()
        # Merge level info
        # if level2:
        #     for k,v in level2.__dict__.items():
        #         if not level.__dict__.get(k,None):
        #             level.__dict__[k]=v
            
        info_provider=GDLevelInfoProvider(level_id)
        info_provider.set_gd_entry(level2,None)
        info_provider.fetch(True,gddl_level.is_plat())
        info_provider.set_GDDL(gddl_level)
        
        info_image=False
        # Image Sections
        if enable_image:
            req_id_base=bbot_api.getid(event)
            imargs=LevelLargeRenderArgs()
            
            info_provider.fillRenderArgs(imargs)
            
            imargs.thumbnail=getThumbnailUrl(level_id) if plugin_cfg.render_server_uri.startswith("ws") else thumb or ""
            
            img=await render_api.render(imargs,request_id=f"{req_id_base}_{time.time()//1}")
            if isinstance(img,bytes):
                msg2=bbot_api.TextImageMessage.build(bot)
                msg2.addLine(formatGDDLLevel(gddl_level,True,False))
                msg2.addImage(img)
                info_image=True
                await msg2.send(gddlsearch)
                
        if show_thumbnail and thumb:
            lines.addImage(thumb)
        # Basic Info (Text)
        if not info_image:
            lines.addLine(formatGDDLLevel(gddl_level,True,False))
        
        if not verbose:
            lines.addLine(f"-v 参数查询具体时长, 上传/更新日期, 及额外曲目.")
        
        for l in info_provider.getTextDescription(info_image):
            lines.addLine(l)

        if lines.msg.__len__():
            await gddlsearch.finish(await bbot_api.auto_pack_message(bot,lines.msg,6))
        
    except Exception as e:
        if isinstance(e,MatcherException):
            raise e
        await gddlsearch.finish(f"出错: {e}")

from ..gdhelp import GD_HELP
@GD_HELP.addHelpFunc
def get_help(bot:Bot,event:Event):
    return ["gddlsearch [参数] [关名/ID] 通过GDDL搜索关卡"]