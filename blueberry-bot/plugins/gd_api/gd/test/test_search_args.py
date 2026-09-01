import pytest
from plugins.gd_api.gd.search_args import LevelSearchArgs, LevelSearchType
from plugins.gd_api.gd.models import Difficulty, Length
from plugins.gd_api.gd import getLevelSearch_async

@pytest.mark.asyncio
async def test_search_args():
    args = (LevelSearchArgs()
        .setSearchType(LevelSearchType.RECENT)
        .setSearch("")
        .setDifficulty([Difficulty.ANY_DEMON])
        .setLength([Length.PLAT])
    )
    args.star = True
    print(args.getData())
    
    print(await getLevelSearch_async(args))
