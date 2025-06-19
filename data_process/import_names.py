import os,sys,json

sys.path.append(".")

from utils.constants import *
import bot_data.data as data

mapPaths={}

with open(MAP_PATHS_FILE,"r") as f:
    mapPaths:dict=json.load(f)    
print(mapPaths)

with open(MAP_NAMES_FILE,"r") as f:
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
    
    if mapName not in mapDataList.keys():
        mapDataList[mapName]={}
        
    if len(mapDataList[mapName].get("filePath"))==0:
        mapDataList[mapName]["filePath"]=mapPaths[mapName]
    mapDataList[mapName]["answer"]=mapName
    mapDataList[mapName]["aliases"]=mapData["alias"]

for name,path in mapPaths.items():
    if(name not in mapDataList.keys()):
        mapDataList[name]={
        "filePath":path,
        "answer":name,
        "aliases":[name]
        }
    mapDataList[name]["filePath"]=path
    
# with open(MAP_PATHS_FILE,"w") as f:
#     json.dump(mapPaths,f,indent=2,ensure_ascii=False)   
    
with open(MAP_NAMES_FILE,"w") as f:
    json.dump(mapDataList,f,indent=2,ensure_ascii=False)