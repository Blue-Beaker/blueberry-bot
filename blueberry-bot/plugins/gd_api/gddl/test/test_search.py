import pytest
from plugins.gd_api.gddl.search import searchGDDLLevel,getGDDLLevel
from plugins.gd_api.gddl.search_args import GDDLSearchArgs,Difficulty,Sort,SortDir

@pytest.mark.asyncio
async def test_search_args():
    args=GDDLSearchArgs()
    args.difficulty=Difficulty.EXTREME
    args.sort=Sort.ENJOYMENT
    args.has_skillset=2
    
    levels,_ = await searchGDDLLevel(args)
    print(levels)
    
@pytest.mark.asyncio
async def test_search_level():
    level,_,_,_ = await getGDDLLevel(97906220)
    print(level.__dict__)