from pydantic import BaseModel, field_validator

class Config(BaseModel):
    enable_dimensional_tp:bool=False