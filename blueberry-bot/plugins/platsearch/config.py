from pydantic import BaseModel, field_validator

class Config(BaseModel):
    sheets_api_key:str=""