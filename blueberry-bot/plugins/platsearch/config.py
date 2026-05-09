from pydantic import BaseModel, field_validator

class Config(BaseModel):
    sheets_api_key:str=""
    sheets_update_interval:int=3600