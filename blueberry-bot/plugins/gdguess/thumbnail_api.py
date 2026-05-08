import os
import requests
from cachetools import cached, TTLCache

@cached(cache=TTLCache(maxsize=20,ttl=600))
def getThumbnail(levelID:int,api_base:str="https://levelthumbs.prevter.me/thumbnail/"):
    headers = {
        "User-Agent": ""
    }
    
    req = requests.get(url=api_base+str(levelID), headers=headers)
    if req.status_code!=200:
        return None
    return req.content
        
if __name__ == "__main__":
    os.makedirs("gdguess_data/images",exist_ok=True)
    img=getThumbnail(127917376)
    if img:
        with open(f"gdguess_data/images/{127917376}.webp","wb") as f:
            f.write(img)