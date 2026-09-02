import pytest
from plugins.gd_api.gddl import parseLevelData, getGDDLPlat_async
from plugins.gd_api.gddl.gddl_internal import getGDDLResponse
from plugins.gd_api.gddl.gddl_cache import CACHE

@pytest.mark.asyncio
async def test_cache_update():
    resp=await CACHE.updateNow()
    print(resp)