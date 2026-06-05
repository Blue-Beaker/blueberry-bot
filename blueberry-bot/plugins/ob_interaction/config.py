from pydantic import BaseModel, field_validator

class Config(BaseModel):    
    ob_poke_back_chance: float=0.6
    ob_poke_cooldown: float=20.0