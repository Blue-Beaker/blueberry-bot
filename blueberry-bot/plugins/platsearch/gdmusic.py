import asyncio
from nonebot import logger, on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot import require
from nonebot.adapters.discord import Bot as DCBot
from nonebot.adapters.onebot.v11 import Bot as OBBot, MessageSegment as OBMessageSegment
from nonebot.internal.adapter import Event,Bot
from nonebot.exception import FinishedException
import httpx

require("bbot_api")
from ..bbot_api.argparse import ArgParser
from ..bbot_api import message_compat
require("gd_api")
from ..gd_api.gd import getSong

try:
    require("orb_api")
    from .. import orb_api
except:
    orb_api=None

gdmusic = on_command("gdmusic")
@gdmusic.handle()
async def _(bot:OBBot|DCBot,event:Event,args: Message = CommandArg()):
    text_args=args.extract_plain_text().split()
    try:
        parser=ArgParser("gdmusic")
        parser.add_argument("-d",action="store_true",help="Download music")
        parser.add_argument("music_id",type=int)
        
        parsed=parser.parse_args(text_args)
        
        music_id=int(parsed.music_id)
        download_music=bool(parsed.d)
        
    except Exception as e:
        await gdmusic.finish(f"错误: {e}")
        
    music=None
    link=None
    
    song_def=getSong(music_id)
    if not song_def or song_def.id<0:
        await gdmusic.finish(f"未找到曲目, 或发生错误. ")
        
    msg=f"{song_def.name}\nBy: {song_def.artistName}\nSongID: {song_def.id} Size:{song_def.size:.2f}MB"
    
    orb_cost=round(song_def.size*5)
    
    if not download_music:
        if isinstance(bot,OBBot):
            msg+=f"\n-d参数播放本音乐 (最多2分钟, 将消耗 {orb_cost} Orbs)"
        else:
            msg+=f"\n-d参数播放本音乐 (将消耗 {orb_cost} Orbs)"
        await gdmusic.finish(msg)
        
    orb_id=None
    if orb_api:
        orb_id=orb_api.get_orb_owner_id(event)
        if orb_id:
            balance=orb_api.get_balance(orb_id)
            if balance<orb_cost:
                await gdmusic.finish(msg+f"\n你的 Orbs 不足! 需要 {orb_cost}, 你只有 {balance}")
            orb_api.add_balance(orb_id,-orb_cost)
            msg+=f"已消耗 {orb_cost} Orbs."
            
    await gdmusic.send(msg)
    
    async def on_error(error_msg:str=""):
        if orb_api and orb_id:
            orb_api.add_balance(orb_id,orb_cost)
            await gdmusic.finish(error_msg+"\n已退还消耗的 Orbs." if error_msg else "发生错误. 已退还消耗的 Orbs.")
        
        await gdmusic.finish(error_msg or "发生错误.")
    
    if music_id<10000000:
        # Newgrounds
        link=song_def.link
    else:
        link=f"https://geometrydashfiles.b-cdn.net/music/{music_id}.ogg"
        
    try:
        logger.info(f"Fetching music {music_id} from: {link}")
        async with httpx.AsyncClient(timeout=30) as client:
            resp=await client.get(link)
        if resp.status_code!=200:
            logger.error(f"连接出错: {resp.status_code}")
            await on_error(f"连接出错: {resp.status_code}")
        if not isinstance(resp.content,bytes):
            logger.error(f"resp.content is not bytes: {type(resp.content)}")
            await on_error(f"发生错误.")
        music=resp.content
        logger.info(f"Got music {music_id}")
            
        if not music:
            logger.error(f"music is empty.")
            await on_error()
            return
        
        if isinstance(bot,OBBot):
            ffmpeg_args=["ffmpeg", "-i", "pipe:0", "-t", "120", "-c:a", "libvorbis", "-f", "ogg", "pipe:1"]
        else:
            ffmpeg_args=["ffmpeg", "-i", "pipe:0", "-c:a", "libvorbis", "-f", "ogg", "pipe:1"]
        
        proc=await asyncio.create_subprocess_exec(
            *ffmpeg_args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout,stderr=await proc.communicate(input=music)
        if proc.returncode!=0:
            logger.error(f"ffmpeg error: {stderr.decode(errors='ignore')}")
            await on_error("音频处理失败.")
        music=stdout
        
        await gdmusic.finish(message_compat.record(bot,music,f"{music_id}.ogg"))
        
    except Exception as e:
        if isinstance(e,FinishedException):
            raise e
        else:
            await on_error()
            logger.error(e)
            
def get_help(bot:Bot,event:Event):
    if isinstance(bot,OBBot) or isinstance(bot,DCBot):
        return ["gdmusic [ID] 查询/点播GD音乐"]
    else:
        return []