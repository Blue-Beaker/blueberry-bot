from pydantic import BaseModel, field_validator

class Config(BaseModel):
    mc_ops:list[str]=[]