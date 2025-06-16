
import json

from nonebot import logger
from .guess_core import GuessManager


CONFIG_PATH="config.json"

server_prefixes:dict[str,str]={}
ops:list[str]=[]
guesses_per_info:int=1
starting_info:int=1

with open(CONFIG_PATH,"r") as f:
    configFile:dict=json.load(f)
    guessSection=configFile.get("guess",{})
    guesses_per_info=guessSection.get("guesses_per_info")
    starting_info=guessSection.get("starting_info")

logger.info(f"loaded config: {guessSection}")

async def run_command(cmd:str,guessManager:GuessManager)->str|None:
    if cmd.startswith("guess"):
        return guess_command(cmd.removeprefix("guess").strip(),guessManager)

def after_command():
    pass

def guess_command(cmd:str,manager:GuessManager)->str|None:
    if cmd.startswith("start"):
        result= manager.start()
    elif cmd.startswith("giveup"):
        result= manager.cancel()
    else:
        result= manager.do_guess(cmd)
    after_command()
    return result
    
class GuessManagerInstances:
    guessManagers:dict[str,GuessManager]={}
    def getOrCreateGuessManager(self,key:str):
        manager = self.guessManagers.get(key,None)
        if manager:
            manager.guesses_per_info=guesses_per_info
            manager.starting_info=starting_info
            return manager
        self.guessManagers[key]=GuessManager()
        return self.guessManagers[key]
    
    def dump(self):
        dumpData={}
        for id,manager in self.guessManagers.items():
            # 不存储空的管理器
            if manager.has_session():
                dumpData[id]=manager.dump()
        return dumpData
    
    def load(self,dumpData:dict[str,dict]):
        for id,manager in dumpData.items():
            self.guessManagers[id]=GuessManager.load(manager)

INSTANCES = GuessManagerInstances()