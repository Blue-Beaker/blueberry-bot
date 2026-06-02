from pydantic import BaseModel, field_validator

class Config(BaseModel):
    sheets_update_interval:int=3600
    render_server_uri:str="ws://localhost:9080"