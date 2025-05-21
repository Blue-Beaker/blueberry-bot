import os,sys,json
os.chdir(sys.path[0])
import data
mapPaths={}

with open("mapPaths.json","r") as f:
    mapPaths:dict=json.load(f)    
print(mapPaths)

with open("data.json","r") as f:
    mapDataList:dict=json.load(f)    
print(mapDataList)

maps=data.maps.copy()
def sort(d:dict):
    return d["file_path"]
    
maps.sort(key=sort)


for mapData in maps:
    mapName=mapData["answer"]
    if mapName not in mapPaths.keys():
        mapPaths[mapName]=""
        
    mapDataList[mapName]={
        "filePath":mapPaths[mapName],
        "answer":mapName,
        "aliases":mapData["alias"]
        }

for name,path in mapPaths.items():
    if(name not in mapDataList.keys()):
        mapDataList[name]={
        "filePath":path,
        "answer":name,
        "aliases":[name]
        }
    mapDataList[name]["filePath"]=path
# with open("mapPaths.json","w") as f:
#     json.dump(mapPaths,f,indent=2,ensure_ascii=False)   
    
with open("data.json","w") as f:
    json.dump(mapDataList,f,indent=2,ensure_ascii=False)