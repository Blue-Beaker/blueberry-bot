import pytest
from plugins.gd_api.gddl.search import searchGDDLLevel
from plugins.gd_api.gddl.search_args import GDDLSearchArgs,Difficulty,Sort,SortDir

@pytest.mark.asyncio
async def test_search_args():
    args=GDDLSearchArgs()
    args.difficulty=Difficulty.EXTREME
    args.sort=Sort.ENJOYMENT
    args.has_skillset=2
    
    levels = await searchGDDLLevel(args)
    print(levels)