import asyncio
from nonebot import on_command,logger,get_plugin_config
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg
from nonebot.exception import MatcherException
from nonebot import get_driver,require

from .config import Config
from .utils import repr_level
from .gd_data import PLAT_CHART_CACHE,AREDL_CACHE

require('bbot_api')
from .. import bbot_api
from ..bbot_api.argparse import ArgParser
require('gd_api')
from ..gd_api.gd import getLevelSearch2_async,LevelSearchType,downloadLevel2_async,LevelSearchArgs,Difficulty,Length,getLevelsFromUser_async,getSong_async
from ..gd_api import gd
from ..gd_api.gd import Level
from ..gd_api.thumbs import getThumbnail_async,getThumbnailUrl
from ..gd_api.gddl.search import getGDDLLevel

require("bbot_perms")
from ..bbot_perms import get_perms

from .utils import repr_level,ensure_gd_level,SearchException
from . import utils

from .gdsearch_backend import GDLevelInfoProvider

def get_level_line(level:Level) -> str:
    levelstr=repr_level(level)
    if level.is_plat():
        levelstr+=("".join([f" E{l2.enj or '-'} W{l2.weight or '-'} P{l2.pemon or '-'}" for l2 in PLAT_CHART_CACHE.get_for_id(level.id)]))
    if level.demon:
        aredl_levels=AREDL_CACHE.get_for_id(level.id)
        if aredl_levels:
            l2=aredl_levels[0]
            levelstr+=f" A#{l2.position}"
    return levelstr

utils.REPR_LEVEL_FUNC=get_level_line

try:
    require("orb_api")
    from .. import orb_api
except:
    orb_api=None
    
driver=get_driver()
plugin_cfg=get_plugin_config(Config)

require('bbot_render')
from ..bbot_render import RenderAPI
from ..bbot_render.models import LevelLargeRenderArgs
render_api=RenderAPI(uri=plugin_cfg.render_server_uri)

_DIFFICULTY_MAPPINGS:dict[str,Difficulty]={
}
_LENGTH_MAPPINGS:dict[str,Length]={l.name.lower():l for l in Length}

def update_diff_aliases():
    _DIFFICULTY_MAPPINGS.update({k.name.lower():k for k in Difficulty})
    
    ALIASES={
        Difficulty.EASY_DEMON:["ezd","ezp"],
        Difficulty.MEDIUM_DEMON:["med","mep"],
        Difficulty.HARD_DEMON:["hdd","hdp"],
        Difficulty.INSANE_DEMON:["insd","insp"],
        Difficulty.EXTREME_DEMON:["exd","exp"],
        Difficulty.ANY_DEMON:["demon","pemon","d"],
        Difficulty.AUTO:["at"],
        Difficulty.EASY:["ez"],
        Difficulty.NORMAL:["nm"],
        Difficulty.HARD:["hd"],
        Difficulty.HARDER:["hr"],
        Difficulty.INSANE:["in"]
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
        
_SEARCH_TYPES:dict[str,SearchTypeArg]={
    "search":SearchTypeArg(LevelSearchType.SEARCH,"Search (Default)"),
    "user":SearchTypeArg(LevelSearchType.FROM_USER,"User's Levels"),
    "recent":SearchTypeArg(LevelSearchType.RECENT,"Recent"),
    "downloads":SearchTypeArg(LevelSearchType.DOWNLOADS,"Most Downloaded"),
    "likes":SearchTypeArg(LevelSearchType.LIKES,"Most Liked"),
    "trending":SearchTypeArg(LevelSearchType.TRENDING,"Trending"),
    "awarded":SearchTypeArg(LevelSearchType.AWARDED,"Awarded"),
    "daily":SearchTypeArg(LevelSearchType.DAILY,"Daily Levels"),
    "weekly":SearchTypeArg(LevelSearchType.WEEKLY,"Weekly Levels"),
    "featured":SearchTypeArg(LevelSearchType.FEATURED,"Featured Levels"),
}

class BoolFlagArg:
    attr_name:str
    help_str:str
    def __init__(self,attr_name:str,help_str:str) -> None:
        self.attr_name=attr_name
        self.help_str=help_str
    def apply(self,searchArgs:LevelSearchArgs,value:bool):
        setattr(searchArgs,self.attr_name,bool(value))

_BOOL_FLAGS:dict[str,BoolFlagArg]={
    "--2-player":BoolFlagArg("twoPlayer","2-Player"),
    "--coins":BoolFlagArg("coins","Has Coins"),
    "--featured":BoolFlagArg("featured","Featured"),
    "--epic":BoolFlagArg("epic","Epic"),
    "--legendary":BoolFlagArg("legendary","Legendary"),
    "--mythic":BoolFlagArg("mythic","Mythic"),
    "--nostar":BoolFlagArg("noStar","No Star (Unrated)"),
    "--original":BoolFlagArg("original","Original")
}

update_diff_aliases()

gdsearch = on_command("gdsearch")
@gdsearch.handle()
async def _(bot:Bot, event:Event, args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    try:
        searchArgs=LevelSearchArgs()
        
        parser=ArgParser("gdsearch")
        
        group_length=parser.add_mutually_exclusive_group()
        group_length.add_argument('--classic',help='Classic only',action='store_true')
        group_length.add_argument('--plat',help='Platformer only',action='store_true')
        
        group_length.add_argument('-l',help='length',type=str,default="")
        
        parser.add_argument('--song',help='Song ID (prefix _ for official songs)',type=str,default="")
        
        parser.add_argument('-d',help='Difficulty',type=str,default="")
        parser.add_argument('-v',help='Show Other Info (Time, Upload/Update date, ...)',action='store_true')
        parser.add_argument('--text',help='Plain Text',action='store_true')
        parser.add_argument('-i',help='Show Thumbnail',action='store_true')
        parser.add_argument('-a',help='Include Unrated',action='store_true')
        parser.add_argument('-u',help="User's Levels",action='store_true')
        
        parser.add_argument('-p',help='Page',type=int,default=0)
        
        parser.add_argument('-t', type=str, help=f"search type ({' | '.join(_SEARCH_TYPES)})", default='search')
        
        filters=parser.add_argument_group("Search Filters")
        for key,entry in _BOOL_FLAGS.items():
            filters.add_argument(key,help=entry.help_str,action='store_true')
        
        parser.add_argument('search', nargs='*', type=str, help='search string')
        parsed=parser.parse_args(raw_args)
        
        search=" ".join(parsed.search)
        searchArgs.setSearch(search)
        
        classic_only=bool(parsed.classic)
        plat_only=bool(parsed.plat)
        
        song_arg=str(parsed.song)
        if song_arg:
            song_id=int(song_arg.removeprefix("_"))
            searchArgs.setSong(song_id,not song_arg.startswith("_"))
        
        if parsed.u:
            search_type_str="user"
        else:
            search_type_str=str(parsed.t).lower()
            
        search_type=_SEARCH_TYPES.get(search_type_str)
            
        if not search_type:
            raise ValueError(f"未知搜索类型 {search_type_str}. 可用类型: {','.join(_SEARCH_TYPES.keys())}")
        
        searchArgs.setSearchType(search_type.search_type)
                
        for key,entry in _BOOL_FLAGS.items():
            name=key.removeprefix("-").removeprefix("-").replace("-","_")
            if getattr(parsed,name):
                entry.apply(searchArgs,True)
        
        lengths:list[Length]=[]
        
        for l in str(parsed.l).lower().split(","):
            if l in _LENGTH_MAPPINGS:
                lengths.append(_LENGTH_MAPPINGS[l])
        
        difficulty:list[Difficulty]=[]
        
        for diff in str(parsed.d).lower().split(","):
            if diff in _DIFFICULTY_MAPPINGS:
                difficulty.append(_DIFFICULTY_MAPPINGS[diff])
                if diff.endswith("p") or diff=="pemon":
                    plat_only=True
        
        logger.info(locals())
        
        include_unrated=bool(parsed.a or parsed.nostar)
        page=int(parsed.p)
        
        if classic_only:
            searchArgs.setLength([Length.TINY,Length.SHORT,Length.MEDIUM,Length.LONG,Length.XL])
        elif plat_only:
            searchArgs.setLength([Length.PLAT])
        else:
            searchArgs.setLength(lengths)
            
        searchArgs.setDifficulty(difficulty)
        searchArgs.setStar(not include_unrated)
        searchArgs.setPage(page)
        
        verbose=bool(parsed.v)
        force_text=bool(parsed.text)
        show_thumbnail=bool(parsed.i)
        
        logger.info(searchArgs.getData())
        
    except Exception as e:
        await gdsearch.finish(str(e))
        return
    
    lines=bbot_api.TextImageMessage.build(bot)
    
    await bbot_api.trigger_typing(bot,event)
    
    if searchArgs.getSearchType()==LevelSearchType.FROM_USER:
        levels,pageinfo=await getLevelsFromUser_async(searchArgs)
    else:
        levels,pageinfo=await getLevelSearch2_async(searchArgs)
        
    if not include_unrated and not str.isdecimal(search):
        lines.addLine("默认只搜索 Rated 关卡. -a 以搜索全部关卡.")
        
    if levels and not get_perms(event).gd_unrated:
        levels = [censor_unrate_levels(l) for l in levels]
    
    try:
        level = ensure_gd_level(levels,pageinfo)
    except SearchException as e:
        await gdsearch.finish(await bbot_api.auto_pack_message(bot,e.msg,6))
        return
    
    
    supports_image=bbot_api.supportsImage(bot)
    show_thumbnail = (show_thumbnail and supports_image)
    enable_image=(not force_text) and supports_image
    
    level2=None
    thumb=None
    song=None
    gddl_level=None
    
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
                    level2,result=await downloadLevel2_async(level.id)
                    if level2 and level2.level_string:
                        cost=min(25,level2.level_string.__len__()//100000)
                        orb_account.add(-cost)
                        lines.addLine(f"已消耗 {cost} Orbs.")
                    elif result:
                        lines.addLine(f"获取完整信息失败: {result.error}")
            else:
                level2,result=await downloadLevel2_async(level.id)
                if (not level2) and result:
                    lines.addLine(f"获取完整信息失败: {result.error}")
            return level2
        
        async def gather_thumbnail():
            if show_thumbnail or enable_image:
                return await getThumbnail_async(level.id)
            return None
            
        async def gather_song():
            song=await getSong_async(level.songID,level.official_song)
            return song
        
        async def gather_gddl():
            if not level.demon:
                return None
            gddl_level,e1,e2,e3=await getGDDLLevel(level.id)
            if e1:
                lines.addLine(f"获取关卡出错: {e1}")
            if e2:
                lines.addLine(f"获取Tags出错: {e2}")
            if e3:
                lines.addLine(f"获取Eligible出错: {e3}")
            return gddl_level
        
        level2, thumb, song, gddl_level = await asyncio.gather(gather_level2(),gather_thumbnail(),gather_song(),gather_gddl())
            
        info_provider=GDLevelInfoProvider(level.id)
        info_provider.fetch(level.demon,level.is_plat())
        info_provider.setGDDL(gddl_level)
        
        info_image=False
        # Image Sections
        if enable_image:
            req_id_base=bbot_api.getid(event)
            imargs=LevelLargeRenderArgs(req_id_base+"_base")
            
            info_provider.fillRenderArgs(imargs)
            
            imargs.level_id=level.id
            imargs.thumbnail=getThumbnailUrl(level.id) if plugin_cfg.render_server_uri.startswith("ws") else thumb or ""
            
            imargs.level_name=level.name
            imargs.song_id=level.songID
            imargs.song_author=song.artistName if song else "Unknown"
            imargs.song_name=song.name if song else "Unknown"
            imargs.creator=level.creator
            imargs.stars=level.stars
            imargs.length=level.get_length().get_name()
            imargs.difficulty=level.get_difficulty().value
            imargs.feature_level=level.epic+1 if level.featured>0 else 0
            imargs.is_plat=level.is_plat()
            imargs.coins=level.coins
            imargs.bronze_coins=not level.verifiedCoins
            imargs.downloads=level.downloads
            imargs.likes=level.likes
            imargs.description=level.get_description()
            
            if level2:
                imargs.length2=format_verify_time(level2.verification_time)
                imargs.song_info=f"Songs: {len(level2.song_ids or '')}, SFXs: {len(level2.sfx_ids or '')}"
            
            img=await render_api.render(imargs)
            if isinstance(img,bytes):
                msg2=bbot_api.TextImageMessage.build(bot)
                msg2.addLine(repr_level(level))
                msg2.addImage(img)
                info_image=True
                await msg2.send(gdsearch)
                
        if show_thumbnail and thumb:
            lines.addImage(thumb)
        # Basic Info (Text)
        if not info_image:
            lines.addLine(repr_level(level))
        
        if not verbose:
            lines.addLine(f"-v 参数查询具体时长, 上传/更新日期, 及额外曲目.")
            
            
        lines.addLine(f"Version: {level.version} Game ver.: {level.game_version}")
        lines.addLine(f"2P: {level.two_player}, Objects: {level.objects}")
        
        if song:
            lines.addLine(f"Song: {song.name} by {song.artistName} ({song.id})")
        
        if not info_image:
            lines.addLine(f"Length: {gd.Length(level.length).name}")
            if level2:
                lines.addText(f" ({format_verify_time(level2.verification_time)})")
                
            lines.addLine(f"Coins: {level.coins}")
            if not level.verifiedCoins:
                lines.addText(" (Bronze)")
                
            if level2:
                lines.addLine(f"Songs: {len(level2.song_ids or '')}, SFXs: {len(level2.sfx_ids or '')}")
            
        if level2:
            lines.addLine(f"Upload/update: {level2.upload_date}/{level2.update_date}")
        
        for l in info_provider.getTextDescription(info_image):
            lines.addLine(l)

        if lines.msg.__len__():
            await gdsearch.finish(await bbot_api.auto_pack_message(bot,lines.msg,6))
        
    except Exception as e:
        if isinstance(e,MatcherException):
            raise e
        await gdsearch.finish(f"出错: {e}")

from .gdhelp import GD_HELP
@GD_HELP.addHelpFunc
def get_help(bot:Bot,event:Event):
    return ["gdsearch [参数] [关名/ID] 搜索关卡"]

def censor_unrate_levels(level:Level):
    level1=Level()
    level1.__dict__=level.__dict__.copy()
    if is_unrated_hidden(level1):
        level1.name="<Unrated Level>"
        level1.description=""
    return level1

def is_unrated_hidden(level:gd.Level):
    return level.stars==0 and level.downloads<5000

def format_verify_time(frame_count: int | None, fps: int = 240) -> str:
    """将验证用时（帧）格式化为 1h 1m 1s 形式，低于 1h/1m 时隐藏对应段落。"""
    if frame_count is None:
        return ""
    total_sec = frame_count // fps
    h = total_sec // 3600
    m = (total_sec % 3600) // 60
    s = total_sec % 60
    parts = []
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    if s or not parts:
        parts.append(f"{s}s")
    return " ".join(parts)