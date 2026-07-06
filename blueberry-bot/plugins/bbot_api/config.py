from pydantic import BaseModel, field_validator

class Config(BaseModel):
    sheets_api_key:str=""
    ob_user_id:int=0
    ob_user_nickname:str=""
    ob_pack_message:bool=False