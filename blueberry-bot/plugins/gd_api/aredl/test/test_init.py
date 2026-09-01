import pytest
from plugins.gd_api.aredl import getAREDLLevels_async

@pytest.mark.asyncio
async def test_get_aredl_levels():
    print(await getAREDLLevels_async())
    print(await getAREDLLevels_async(True))
