#!/usr/bin/python3

import random
import shutil
import time,os,sys
import json

sys.path.append(".")

import entity_tag_utils as entity_tag_utils
from entity_tag_utils import EntityCategoryPre,EntityDataManagerPre
from utils.fileUtils import listRecursive
from constants import *

original_workdir=os.getcwd()

#收集要导出的地图json文件列表
def genMapsToExport(source:str,dest:str):
    mapsList=listRecursive(source,".json")
    exportedMapsList=listRecursive(dest,".json")
    # print(mapsList)
    # print(exportedMapsList)
    mapsToExport:dict[str,str]={}
    for map in mapsList:
        outName=map.replace(MAP_RAW_DATA_DIR,MAP_DATA_DIR)
        # if(outName not in exportedMapsList):
        mapsToExport[map]=outName
    return mapsToExport
            
mapsToExport=genMapsToExport(MAP_RAW_DATA_DIR,MAP_DATA_DIR)
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

#处理一面的数据
def processLevel(leveldata:dict,managerPre:EntityDataManagerPre) -> dict:
    entityCount:dict[str,int]={}
    triggerCount:dict[str,int]={}
    entityTagCount:dict[str,int]={}
    
    if("children" in leveldata.keys()):
        for child in leveldata.get("children"): # type: ignore
            if(getName(child)=="entities"):
                entities=child.get("children")
                for entity in entities:
                    increment(entityCount,getName(entity))
                    # 根据实体查找并匹配标签, 计数
                    for entityTag in managerPre.get_categories(getName(entity)):
                        if(entityTag.doesEntityMatch(entity)):
                            increment(entityTagCount,entityTag.id)
                    
                    
            if(getName(child)=="triggers"):
                triggers=child.get("children")
                for trigger in triggers:
                    increment(triggerCount,getName(trigger))
    return {"entities":entityCount,"entityTagCount":entityTagCount,"triggers":triggerCount}
                    
#处理整张地图的数据
def processMapData(mapdata:dict,managerPre:EntityDataManagerPre):
    entityCount:dict[str,int]={}
    triggerCount:dict[str,int]={}
    entityTagCount:dict[str,int]={}
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
                    
                    levelInfo=processLevel(level,managerPre)
                    sumCounts(entityCount,levelInfo["entities"])
                    sumCounts(triggerCount,levelInfo["triggers"])
                    sumCounts(entityTagCount,levelInfo["entityTagCount"])
                    
    # 排序, 方便查询
    entityCount=dict(sorted(entityCount.items(), key=lambda item: item[0]))
    triggerCount=dict(sorted(triggerCount.items(), key=lambda item: item[0]))
    entityTagCount=dict(sorted(entityTagCount.items(), key=lambda item: item[0]))
    
    exportData={}
    exportData["mapName"]=mapName
    exportData["levelCount"]=levelCount
    exportData["levels"]=levelNames
    exportData["fillers"]=fillers
    exportData["entities"]=entityCount
    exportData["entityTagCount"]=entityTagCount
    exportData["triggers"]=triggerCount
    return exportData

def main():

    managerPre=EntityDataManagerPre()
    managerPre.load()
    managerPre.process()
    # print(managerPre.entity_to_categories)
    entityCount:dict[str,int]={}
    triggerCount:dict[str,int]={}

    for inputFile,outputFile in mapsToExport.items():
        
        
        with open(inputFile,"r",encoding="utf-8",errors="ignore") as f:
            mapdata=json.load(f,strict=False)
        exported_data=processMapData(mapdata,managerPre)
        
        
        sumCounts(entityCount,exported_data["entities"])
        sumCounts(triggerCount,exported_data["triggers"])
        
        os.makedirs(os.path.dirname(outputFile),exist_ok=True)
        with open(outputFile,"w") as f2:
            write_data=exported_data.copy()
            json.dump(write_data,f2,indent=2)
            # print(exported_data)
            
        print(os.path.relpath(outputFile,original_workdir))

    entityCount=dict(sorted(entityCount.items(), key=lambda item: item[0]))
    triggerCount=dict(sorted(triggerCount.items(), key=lambda item: item[0]))

    with open(os.path.join(MAP_DATA_DIR,"all_maps.json"),"w") as f3:
        allData={}
        allData["entities"]=entityCount
        # allData["triggers"]=triggerCount
        json.dump(allData,f3,indent=2)

if __name__ == "__main__": 
    main()