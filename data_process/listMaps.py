
import os,sys

sys.path.append(".")

from utils.constants import *

from utils.fileUtils import listRecursive

filesList = listRecursive(MAP_DATA_DIR,".json")
print(filesList)