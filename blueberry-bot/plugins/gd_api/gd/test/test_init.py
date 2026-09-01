import pytest
from plugins.gd_api.gd import getLevel_async

@pytest.mark.asyncio
async def test_get_level():
    print(await getLevel_async("77236592"))
    print(await getLevel_async("126461421"))
