from nonebot.adapters import Event
from nonebot import require

require('gd_api')
from ...gd_api.gd import downloadLevel2_async
from ...gd_api.gd import Level

try:
    require("orb_api")
    from ... import orb_api
except:
    orb_api=None

async def get_download_level(level_id: int, event: Event):
    level2:Level|None=None
    lines:list[str]=[]
    if orb_api:
        orb_account=orb_api.OrbAccount.fromEvent(event)
        if not orb_account:
            return level2,lines
        if orb_account.get()<25:
            lines.append("额外信息需要持有 25 Orbs. 消耗可低于此值.")
        else:
            level2,result=await downloadLevel2_async(level_id)
            if level2 and level2.level_string:
                cost=min(25,level2.level_string.__len__()//100000)
                orb_account.add(-cost)
                lines.append(f"已消耗 {cost} Orbs.")
            elif result:
                lines.append(f"获取完整信息失败: {result.error}")
    else:
        level2,result=await downloadLevel2_async(level_id)
        if (not level2) and result:
            lines.append(f"获取完整信息失败: {result.error}")
    return level2,lines