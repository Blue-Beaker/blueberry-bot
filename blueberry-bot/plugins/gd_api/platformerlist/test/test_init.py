import pytest
from plugins.gd_api.platformerlist import getTPLLevels_async

@pytest.mark.asyncio
async def test_get_tpl_levels():
    print(await getTPLLevels_async())
