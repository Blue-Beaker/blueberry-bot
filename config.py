from pydantic import BaseModel, field_validator

class Config(BaseModel):
    mc_message_prefix: str="[§bBlueberry_Bot§r]"
    mc_ops:list[str]=[]