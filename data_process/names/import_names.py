import os,sys,json
from globals import *

pwd=os.getcwd()
os.chdir(sys.path[0])
import data
os.chdir(pwd)


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
    
with open(MAP_NAMES_FILE,"w") as f:
    json.dump(mapDataList,f,indent=2,ensure_ascii=False)