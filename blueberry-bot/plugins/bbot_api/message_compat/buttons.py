from pydantic import BaseModel

class KBButton(BaseModel):
    text:str
    command:str

class ButtonKeyboard:
    rows:list[list[KBButton]]
    def __init__(self) -> None:
        self.rows=[]
    def addButton(self,text:str,command:str):
        self.addKBButton(KBButton(text=text,command=command))
    def addKBButton(self,button:KBButton):
        if not self.rows:
            self.addLine()
        self.rows[-1].append(button)
    def addLine(self):
        self.rows.append([])