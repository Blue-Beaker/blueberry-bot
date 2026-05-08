from pydantic import BaseModel, field_validator

class Config(BaseModel):
    level_thumbnails_api_base:str="https://levelthumbs.prevter.me/thumbnail/"