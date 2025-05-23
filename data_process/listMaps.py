
import os,sys
from globals import *

os.chdir(sys.path[0])

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

filesList = listRecursive(MAP_DATA_DIR,".json")
print(filesList)