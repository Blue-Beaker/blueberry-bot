import pytest
from plugins.gd_api.pemonlist import getPemonlistLevels_async

@pytest.mark.asyncio
async def test_get_pemonlist_levels():
    print(await getPemonlistLevels_async())
