from pydantic import BaseModel, field_validator

class Config(BaseModel):
    debug_hook_discord:bool=False
    render_server_uri:str="http://localhost:9081"