import pytest
from plugins.gd_api.gddl import parseLevelData, getGDDLPlat_async
from plugins.gd_api.gddl.gddl_internal import getGDDLResponse

@pytest.mark.asyncio
async def test_get_gddl_response():
    resp=await getGDDLResponse()
    if resp:
        levels=parseLevelData(resp.levels)
        print(levels)
        return levels

@pytest.mark.asyncio
async def test_get_gddl_plat_async():
    levels=await getGDDLPlat_async()
    if levels:
        print(levels)
