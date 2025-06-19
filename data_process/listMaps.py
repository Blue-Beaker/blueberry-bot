
import os,sys

sys.path.append(".")

from constants import *

from utils.fileUtils import listRecursive

filesList = listRecursive(MAP_DATA_DIR,".json")
print(filesList)