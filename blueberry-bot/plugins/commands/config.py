from pydantic import BaseModel, field_validator

class Config(BaseModel):
    help_lines_overrides:list[str]=[]