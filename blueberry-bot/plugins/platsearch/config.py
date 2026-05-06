from pydantic import BaseModel, field_validator

class Config(BaseModel):
    sheets_auth_login:bool=False
    sheets_auth_host:str="localhost"
    sheets_auth_port:int=0