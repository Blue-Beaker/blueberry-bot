import os
import pytest
from plugins.gd_api.thumbs import getThumbnail_async

@pytest.mark.asyncio
async def test_get_thumbnail():
    os.makedirs("gdguess_data/images",exist_ok=True)
    img=await getThumbnail_async(127917376)
    if img:
        with open(f"gdguess_data/images/{127917376}.webp","wb") as f:
            f.write(img)
