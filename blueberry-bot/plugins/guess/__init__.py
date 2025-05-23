

import json
import os
from . import guess_data

from . import handler_mc
from . import handler_dc
from . import handler_base

SESSIONS_FILE="guess_sessions.json"

guess_data.load_all_data()

loadEntityCats=[]
for value in guess_data.ENTITY_MANAGER.category_data.values():
    loadEntityCats.append(f"{value.id}={value.name}")
    
print(f"已加载实体类别: {", ".join(loadEntityCats)}")
print(f"已加载地图: {", ".join(guess_data.MAP_MANAGER.map_data.keys())}")

if os.path.exists(SESSIONS_FILE):
    with open(SESSIONS_FILE,"r") as f:
        handler_base.INSTANCES.load(json.load(f))
        print(f'已加载会话: {handler_base.INSTANCES.dump()}')
        
def saveSessions():
    with open(SESSIONS_FILE,"w") as f:
        json.dump(handler_base.INSTANCES.dump(),f,ensure_ascii=False,indent=2)
        
handler_base.after_command=saveSessions
        
try:
    handler_mc.main()
    handler_dc.main()
finally:
    saveSessions()