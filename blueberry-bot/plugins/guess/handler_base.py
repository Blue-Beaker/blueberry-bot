
from .guess_core import GuessManager

async def run_command(cmd:str,guessManager:GuessManager)->str|None:
    if cmd.startswith("guess"):
        return guess_command(cmd.removeprefix("guess").strip(),guessManager)

def guess_command(cmd:str,manager:GuessManager)->str|None:
    if cmd.startswith("start"):
        return manager.start()
    elif cmd.startswith("giveup"):
        return manager.cancel()
    else:
        return manager.do_guess(cmd)
    
class GuessManagerInstances:
    guessManagers:dict[str,GuessManager]={}
    def getOrCreateGuessManager(self,key:str):
        manager = self.guessManagers.get(key,None)
        if manager:
            return manager
        self.guessManagers[key]=GuessManager()
        return self.guessManagers[key]
    
    def dump(self):
        dumpData={}
        for id,manager in self.guessManagers.items():
            dumpData[id]=manager.dump()
        return dumpData
    
    def load(self,dumpData:dict[str,dict]):
        for id,manager in dumpData.items():
            self.guessManagers[id]=GuessManager.load(manager)

INSTANCES = GuessManagerInstances()