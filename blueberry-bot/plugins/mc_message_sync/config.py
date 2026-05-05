from pydantic import BaseModel, field_validator

class Config(BaseModel):
    mc_sync_mappings:dict[str,int]={}
    mc_sync_notice_events:bool=False