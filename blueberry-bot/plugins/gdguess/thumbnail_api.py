import os
import time
from nonebot import logger
import requests
from cachetools import cached, TTLCache

@cached(cache=TTLCache(maxsize=20,ttl=600))
def getThumbnail(levelID:int,api_base:str="https://levelthumbs.prevter.me/thumbnail/",max_tries:int=10):
    headers = {
        "User-Agent": ""
    }
    
    for i in range(max_tries):
        try:
            req = requests.get(url=api_base+str(levelID), headers=headers)
            if req.status_code!=200:
                return None
            return req.content
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Exception getting thumbnail, ({i+1}/{max_tries}): {e}")
            time.sleep(5)
            
    return None
    # return req.content
        
if __name__ == "__main__":
    os.makedirs("gdguess_data/images",exist_ok=True)
    img=getThumbnail(127917376)
    if img:
        with open(f"gdguess_data/images/{127917376}.webp","wb") as f:
            f.write(img)