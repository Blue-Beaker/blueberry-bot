#!/usr/bin/python3

import random
import shutil
import time,os,sys
import json

MAP_FOLDER="map_json"
EXPORT_FOLDER="map_export_data"

def listRecursive(folder:str,suffix:str=""):
    filesList:list[str]=[]
    files=os.listdir(folder)
    files.sort()
    for file in files:
        filepath=os.path.join(folder,file)
        if(os.path.isdir(filepath)):
            filesList.extend(listRecursive(filepath,suffix))
        if(file.endswith(suffix)):
            filesList.append(filepath)
    return filesList


def genMapsToExport(source:str,dest:str):
    mapsList=listRecursive(source,".json")
    exportedMapsList=listRecursive(dest,".json")
    # print(mapsList)
    # print(exportedMapsList)
    mapsToExport:dict[str,str]={}
    for map in mapsList:
        outName=map.replace(MAP_FOLDER,EXPORT_FOLDER)
        # if(outName not in exportedMapsList):
        mapsToExport[map]=outName
    return mapsToExport
            
mapsToExport=genMapsToExport(MAP_FOLDER,EXPORT_FOLDER)
print(mapsToExport)

def increment(d:dict,s:str,c:int=1):
    if(s not in d.keys()):
        d[s]=c
    else:
        d[s]=d[s]+c
    return d

def sumCounts(d1:dict[str,int],d2:dict[str,int]):
    d3:dict[str,int]=d1
    for k,v in d2.items():
        increment(d3,k,v)
    return d3

def getName(child:dict):
    if not isinstance(child,dict):
        print(child)
    if("name" in child.keys()):
        return str(child["name"])
    return "null"

def processLevel(leveldata:dict) -> dict:
    entityCount:dict[str,int]={}
    triggerCount:dict[str,int]={}
    
    if("children" in leveldata.keys()):
        for child in leveldata.get("children"): # type: ignore
            if(getName(child)=="entities"):
                entities=child.get("children")
                for entity in entities:
                    increment(entityCount,getName(entity))
                    
            if(getName(child)=="triggers"):
                triggers=child.get("children")
                for trigger in triggers:
                    increment(triggerCount,getName(trigger))
    return {"entities":entityCount,"triggers":triggerCount}
                    
def processMapData(mapdata:dict):
    entityCount:dict[str,int]={}
    triggerCount:dict[str,int]={}
    levelNames:list[str]=[]
    fillers:list[str]=[]
    levelCount=0
    mapName=mapdata["attributes"]["Package"]
    if("children" in mapdata.keys()):
        for child in mapdata.get("children"): # type: ignore
            if(getName(child)=="levels"):
                levels=child
                for level in levels.get("children"):
                    levelName:str=level["attributes"]["name"]
                    if("filler" not in levelName.lower()):
                        levelCount=levelCount+1
                        levelNames.append(levelName)
                    else:
                        fillers.append(levelName)
                    
                    levelInfo=processLevel(level)
                    sumCounts(entityCount,levelInfo["entities"])
                    sumCounts(triggerCount,levelInfo["triggers"])
                    
    entityCount=dict(sorted(entityCount.items(), key=lambda item: item[0]))
    triggerCount=dict(sorted(triggerCount.items(), key=lambda item: item[0]))
    return {"mapName":mapName,"levelCount":levelCount,"levels":levelNames,"fillers":fillers,"entities":entityCount,"triggers":triggerCount}

entityCount:dict[str,int]={}
triggerCount:dict[str,int]={}

for inputFile,outputFile in mapsToExport.items():
    
    print(inputFile)
    with open(inputFile,"r",encoding="utf-8",errors="ignore") as f:
        mapdata=json.load(f,strict=False)
    exported_data=processMapData(mapdata)
    
    sumCounts(entityCount,exported_data["entities"])
    sumCounts(triggerCount,exported_data["triggers"])
    
    os.makedirs(os.path.dirname(outputFile),exist_ok=True)
    with open(outputFile,"w") as f2:
        json.dump(exported_data,f2,indent=2)
        # print(exported_data)

entityCount=dict(sorted(entityCount.items(), key=lambda item: item[0]))
triggerCount=dict(sorted(triggerCount.items(), key=lambda item: item[0]))
with open(os.path.join(EXPORT_FOLDER,"all_maps.json"),"w") as f3:
    json.dump({"entities":entityCount,"triggers":triggerCount},f3,indent=2)