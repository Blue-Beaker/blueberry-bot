import pytest
from plugins.gd_api.gd import getUser_async

@pytest.mark.asyncio
async def test_get_user():
    print(await getUser_async("robtop"))
    print(await getUser_async("bluebeaker"))
    print(await getUser_async("yeshengxiaozu"))
