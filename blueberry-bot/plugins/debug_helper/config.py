from pydantic import BaseModel, field_validator

class Config(BaseModel):
    debug_sessions:list[str]=[]
    debug_sessions_is_on:bool=False
    
    debug_always_allowed_plugins:list[str]=[]