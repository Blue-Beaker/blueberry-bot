import pytest
from plugins.gd_api.gddl import parseLevelData
from plugins.gd_api.gddl.gddl_internal import getGDDLResponse

@pytest.mark.asyncio
async def test_get_gddl_response():
    resp=await getGDDLResponse()
    if resp:
        levels=parseLevelData(resp.levels)
        print(levels)
        return levels
