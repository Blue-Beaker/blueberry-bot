

from . import guess_data

from . import handler_mc
from . import handler_dc

guess_data.load_all_data()

loadEntityCats=[]
for value in guess_data.ENTITY_MANAGER.category_data.values():
    loadEntityCats.append(f"{value.id}={value.name}")
    
print(f"已加载实体类别: {", ".join(loadEntityCats)}")
print(f"已加载地图: {", ".join(guess_data.MAP_MANAGER.map_data.keys())}")

handler_mc.main()
handler_dc.main()
