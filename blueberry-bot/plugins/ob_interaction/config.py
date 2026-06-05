from pydantic import BaseModel, field_validator

class Config(BaseModel):    
    ob_poke_back_chance: float=0.6